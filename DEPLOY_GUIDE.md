# Literature Screening Agent 部署指南

仓库：`3076858120/Literature-Screening-Agent`

## 1. 克隆

```bash
git clone https://github.com/3076858120/Literature-Screening-Agent.git
cd Literature-Screening-Agent
```

## 2. 本地环境

- Windows / macOS / Linux
- Python 3.7+
- Zotero Desktop
- Zotero Connector
- Chrome 或 Edge
- Web of Science 合法访问权限

本项目的 `scripts/zotero_api.py` 不需要额外 Python 第三方依赖。

## 3. 测试 Zotero

启动 Zotero Desktop 后：

```bash
python scripts/zotero_api.py ping
```

如果正常，应看到 HTTP 200 和 Zotero 在线状态。

## 4. 使用 Agent

将仓库中的 `SKILL.md` 放入你使用的 AI Agent 的技能目录。随后给 Agent 提供：

- 研究主题
- 相关性判断标准
- WoS 检索式或已经打开的结果会话
- Zotero 目标集合
- 起始/结束记录号（如需要）

示例：

```text
请从当前 Web of Science 结果中筛选与“数据中心水资源影响”相关的文献，
相关文献保存到 Zotero 的“数据中心水资源”集合，并尽量获取 PDF。
从第 1 条开始，逐篇筛选，不要跳过记录。
```

## 5. 本地 CLI

### 检查集合

```bash
python scripts/zotero_api.py check -c "我的集合"
```

### 保存题录

```bash
python scripts/zotero_api.py save -i paper.json
```

## 6. 不要提交的数据

公开仓库不应包含：

- `zotero.sqlite` / `.zref.sqlite`
- 个人 Zotero 数据库
- 实际筛选结果
- 完整文献标题清单
- 私有研究数据
- API Token、密码或 Cookie

仓库中的 `.gitignore` 已针对这些常见情况进行配置。

## 7. PDF 获取说明

Agent 采用逐级策略：

1. 可用 PDF / EndNote Click
2. Publisher 全文页面
3. Publisher 的网页版 PDF
4. 无法获得全文时只保存题录并记录

PDF 是否能够获取取决于机构订阅、开放获取状态、出版商访问策略以及 CAPTCHA / Cloudflare 等因素。

## 8. 运行原则

Agent 在浏览器中执行操作时，应在每次关键点击前重新确认当前页面状态；不要依赖过期坐标。遇到 CAPTCHA，应暂停自动化并让用户完成验证。
