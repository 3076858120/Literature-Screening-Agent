---
name: wos-zotero-literature-agent
description: 通用 Web of Science → Zotero 文献搜集 Agent：按任意研究主题逐篇筛选 WoS 检索结果、判断相关性、保存题录并按三级策略抓取 PDF 全文。Use whenever the user asks to 搜集文献 / 筛选保存 / 继续筛选 / 从 WoS 下载文献 PDF / 把检索结果存进 Zotero — for any research topic, even if they just say “继续” in a session where this workflow is running.
---

# WoS → Zotero 逐篇文献搜集（题录 + 三级 PDF 提取）

在用户自己的 Chrome（装 Zotero Connector）+ Zotero 桌面端运行的前提下，按研究主题逐篇读取 WoS 检索结果、判断相关性、保存题录，并按三级策略尽量抓取 PDF。**用户会随时看屏幕或改动窗口，每步动作前必须重新截图确认；除非用户明示，不要跳过任何记录（一片一片来）。**

## 0. 会话参数（开始时与用户确认，记入进度文件）

- **研究主题与相关性判断标准**（决定“保存 / 跳过”）。
- **Zotero 目标集合**（保存目标 = Zotero 当前选中集合，窗口标题可见）。
- **检索式 / 结果会话 URL**（决定从哪批结果里筛）。
- **起止记录号**（默认第 1 条到末尾；断点续筛从上次停处继续）。
- 进度文件：在用户工作目录维护 `筛选进度.md`（已处理区间、已存清单、跳过清单、无 PDF 名单），每次汇报后更新。

## 1. 环境前置（每次都要确认）

1. 用 computer-use 绑定**用户的 Chrome**——Zotero 连接器只装在里面；不要用内置浏览器。
2. **Zotero 桌面端必须在运行**：探测 `http://127.0.0.1:23119/connector/ping`，返回 “Zotero is running”。保存目标 = Zotero 当前选中集合。
3. WoS 走机构 IP 权限（例如 webofscience.clarivate.cn），一般无需个人账号。
4. 数据库验证（以 Zotero 数据目录 `zotero.sqlite` 为准，先复制再查，运行时有锁）：
   - Zotero 数据目录默认 `~/Zotero`，自定义时读取 `%APPDATA%/Zotero/Zotero/Profiles/*/prefs.js` 中的 `extensions.zotero.dataDir`；
   - 集合条目数（排除回收站）：`collectionItems × collections(集合名)`，加 `itemID NOT IN (SELECT itemID FROM deletedItems)`；
   - 某条目是否带 PDF：`itemAttachments(parentItemID) contentType='application/pdf'`；
   - 以上已封装为本仓库 `scripts/zotero_api.py check`，可直接调用。

## 2. 恢复检索会话

- 优先重新打开**结果页 URL**（`/wos/woscc/summary/<session-id>/relevance/1`），可恢复记录导航。
- 直接开 `full-record/WOS:xxx` 会脱离会话（显示 “1 of 1”），不要这样进入。
- 会话彻底丢失 → 回高级检索重跑检索式，再点进任一记录。注意：重跑后相关度排序的记录顺序可能与之前不同，**以当前会话顺序为准逐篇走，不要凭记忆跳号**；WoS 偶尔新索引文献导致编号偏移，定位以标题内容为准。

## 3. 逐篇循环（全屏窗口，截图光栅 1280×757）

每条记录：下一条 → 判相关性 → 相关则保存（三级 PDF 策略）→ 下一条。

1. **下一条**：点 “>”（约 (1221, 302)）；保存后第一次点 “>” 常被吞掉，无跳转就再点。跳转指定记录：点计数框（约 (1129, 302)）→ Ctrl+A → 输编号 → Return；失败就用 “>” 连点，并从页面计数确认落点。
2. **判相关性**：读标题（页面加载后等约 2.5s 再截图）；拿不准再滚动读摘要。按会话参数里的标准判断；**拿不准时倾向跳过并记入“待复核”清单**。
3. **相关 → 三级 PDF 提取策略**（顺序不可乱）：
   - **第①级**：在 WoS 记录页等待 EndNote Click / 可用 PDF 提示出现，再点 Zotero Connector → 右上角弹窗 → **点击弹窗里的条目行才真正入库**。
   - **第②级**：第①级失败 → 点记录页 “Free Full Text from Publisher” / “Full text at publisher” 进入出版商页面 → 等加载 → 点 Connector → 点弹窗条目行。
   - **第③级**：第②级失败 → 在出版商页面找 “View PDF” 类按钮进入网页版 PDF → 在 PDF 页点 Connector → 点弹窗条目行。
   - **兜底**：三级都失败（NO ACCESS / Cloudflare / 无 View PDF）→ 只存题录，并记入“难获取 PDF 名单”。
   - 多记录结果页触发 Connector 可能弹出 **Zotero Item Selector**，等待提取完成后 Select All → OK。
4. **CAPTCHA / 人机验证**：出版商跳转、PDF 抓取时可能出现 Cloudflare 验证。发现后停下并让用户完成验证，之后继续。
5. **进度汇报**：每处理约 25 条（或遇到异常）向用户报告：处理到第几条、保存几篇、有 PDF 几篇、无 PDF 名单，并更新进度文件。

## 4. 收尾

1. 将无 PDF 名单交给用户统一处理（记录 DOI / 出版商）。
2. 重复条目在 Zotero “重复条目”面板合并；误存噪声条目从集合移除。
3. 用 `scripts/zotero_api.py check` 复核 PDF 覆盖率并生成最终报告。

## 5. 坐标与稳定性备注

- 浏览器坐标只适用于当前记录的窗口布局；其他分辨率或窗口尺寸必须重新截图定位。
- 窗口尺寸、位置可能变化——**坐标点击前必须重新截图绑定当前画面**；不要依赖过期坐标。
- TabItem 标题可能含实时变化信息，不要依赖标题中的动态数值定位标签页。
- Connector 偶发失灵时，读取记录页元数据（题名/作者/期刊/卷期页/DOI/年份），调用 `scripts/zotero_api.py save` 作为本地 API 兜底。

## 6. 核心相关性原则

相关性标准必须由用户在每次研究任务开始时定义。Agent 不应擅自把某个研究主题的筛选标准硬编码为所有项目的标准。
