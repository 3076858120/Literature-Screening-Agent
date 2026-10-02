#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zotero_api.py — Zotero 本地 Connector API 命令行工具

零第三方依赖，只使用 Python 标准库。需要 Zotero Desktop 正在运行（默认端口 23119）。

子命令:
  ping                     探测 Zotero 本地服务是否在线
  save -i item.json        把翻译器格式的条目 JSON 直接存入当前选中集合
  check -c 集合名           检查集合条目数与 PDF 覆盖率，并列出无 PDF 条目

示例:
  python zotero_api.py ping
  python zotero_api.py save -i paper.json
  echo '{"items":[{...}]}' | python zotero_api.py save
  python zotero_api.py check -c "我的集合"
"""

import argparse
import glob
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import urllib.request

PORT = 23119
BASE = f"http://127.0.0.1:{PORT}"


def cmd_ping(args):
    req = urllib.request.Request(f"{BASE}/connector/ping", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8", "replace")
            print(f"HTTP {resp.status} | {body.strip()}")
            print("Zotero connector server: ONLINE" if resp.status == 200 else "Unexpected status")
            return 0
    except Exception as e:
        print(f"Zotero connector server: OFFLINE ({e})")
        print("请确认 Zotero Desktop 已启动。")
        return 1


def cmd_save(args):
    if args.input and args.input != "-":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
        payload_obj = data
    elif isinstance(data, dict):
        payload_obj = {"items": [data]}
    elif isinstance(data, list):
        payload_obj = {"items": data}
    else:
        print('输入必须是条目对象、条目数组或 {"items": [...]}', file=sys.stderr)
        return 2

    if not payload_obj["items"]:
        print("items 为空，未保存任何条目", file=sys.stderr)
        return 2

    payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/connector/saveItems",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(
                f"HTTP {resp.status} — 已保存 {len(payload_obj['items'])} 个条目"
                f"{' (201=成功)' if resp.status == 201 else ' (非预期状态码，请到 Zotero 核对)'}"
            )
            return 0 if resp.status == 201 else 1
    except Exception as e:
        print(f"保存失败: {e}", file=sys.stderr)
        print("请先 ping 确认 Zotero 在线，并检查 JSON 是否为翻译器格式。", file=sys.stderr)
        return 1


def find_data_dir(explicit):
    if explicit:
        return explicit

    default = os.path.join(os.path.expanduser("~"), "Zotero")
    if os.path.exists(os.path.join(default, "zotero.sqlite")):
        return default

    for prefs in glob.glob(
        os.path.join(
            os.environ.get("APPDATA", ""),
            "Zotero",
            "Zotero",
            "Profiles",
            "*",
            "prefs.js",
        )
    ):
        try:
            with open(prefs, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "extensions.zotero.dataDir" in line:
                        raw = line.split('"')
                        if len(raw) >= 2:
                            path = raw[-2].replace("\\\\", "\\")
                            if os.path.exists(os.path.join(path, "zotero.sqlite")):
                                return path
        except OSError:
            continue
    return None


def cmd_check(args):
    data_dir = find_data_dir(args.data_dir)
    if not data_dir:
        print("未找到 Zotero 数据目录（无 zotero.sqlite）。请用 --data-dir 显式指定。", file=sys.stderr)
        return 1

    db = os.path.join(data_dir, "zotero.sqlite")
    print(f"数据目录: {data_dir}")

    tmp = os.path.join(tempfile.gettempdir(), "zotero_api_check.sqlite")
    try:
        shutil.copy2(db, tmp)
    except PermissionError:
        print("zotero.sqlite 被占用且无法复制，请重试。", file=sys.stderr)
        return 1

    con = sqlite3.connect(tmp)
    cur = con.cursor()
    row = cur.execute(
        "SELECT collectionID FROM collections WHERE collectionName=?",
        (args.collection,),
    ).fetchone()
    if not row:
        names = [r[0] for r in cur.execute("SELECT collectionName FROM collections ORDER BY collectionName")]
        print(f"未找到集合“{args.collection}”。现有集合:", file=sys.stderr)
        for name in names:
            print(f"  - {name}", file=sys.stderr)
        con.close()
        os.remove(tmp)
        return 1

    cid = row[0]
    rows = cur.execute(
        """
        SELECT i.itemID FROM collectionItems ci
        JOIN items i ON i.itemID = ci.itemID
        JOIN itemTypes it ON it.itemTypeID = i.itemTypeID
        WHERE ci.collectionID = ?
          AND it.typeName NOT IN ('attachment','note')
          AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
        """,
        (cid,),
    ).fetchall()

    total, with_pdf, missing = 0, 0, []
    for (iid,) in rows:
        total += 1
        title_row = cur.execute(
            """
            SELECT v.value FROM itemData d
            JOIN fields f ON f.fieldID = d.fieldID AND f.fieldName = 'title'
            JOIN itemDataValues v ON v.valueID = d.valueID
            WHERE d.itemID = ?
            """,
            (iid,),
        ).fetchone()
        pdf = cur.execute(
            """
            SELECT COUNT(*) FROM itemAttachments a
            JOIN items i2 ON i2.itemID = a.itemID
            WHERE a.parentItemID = ? AND i2.itemTypeID != 14
              AND a.contentType = 'application/pdf'
            """,
            (iid,),
        ).fetchone()[0]
        if pdf:
            with_pdf += 1
        else:
            missing.append(title_row[0] if title_row else f"(无标题 itemID={iid})")

    con.close()
    os.remove(tmp)

    print(f"\n集合“{args.collection}”: 共 {total} 条有效条目（已排除回收站）")
    print(f"带 PDF 附件: {with_pdf} 条（{with_pdf * 100 // max(total, 1)}%）")
    if missing:
        print(f"\n无 PDF 的条目（{len(missing)} 条，便于手动补齐）:")
        for title in missing:
            print(f"  - {title}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ping", help="探测 Zotero 本地服务")

    p_save = sub.add_parser("save", help="保存条目 JSON 到当前选中集合")
    p_save.add_argument("-i", "--input", default="-", help="条目 JSON 文件路径；- 或缺省表示 stdin")

    p_check = sub.add_parser("check", help="核对集合条目数与 PDF 覆盖率")
    p_check.add_argument("-c", "--collection", required=True, help="Zotero 集合名")
    p_check.add_argument("--data-dir", default=None, help="Zotero 数据目录（含 zotero.sqlite），缺省自动探测")

    args = ap.parse_args()
    return {"ping": cmd_ping, "save": cmd_save, "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
