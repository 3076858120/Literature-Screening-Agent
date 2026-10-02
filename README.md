# WoS → Zotero Literature Screening Agent

一个“浏览器 Agent 技能 + 零依赖 CLI 工具”组合，用于自动化文献综述中最耗时的环节：在 Web of Science 上按主题逐篇筛选检索结果，把相关文献保存到 Zotero，并尽量获取 PDF 全文。

## 它解决了什么问题

文献综述前期的“逐条看检索结果、判断相关性、存题录、找 PDF”非常耗时。本项目将其拆成两个可复用组件：

1. **Agent 技能**（`SKILL.md`）：驱动具有浏览器操控能力的 AI Agent，逐篇筛选 WoS 结果并保存到 Zotero。
2. **Zotero CLI 工具**（`scripts/zotero_api.py`）：只依赖 Python 标准库，可直接调用 Zotero 本地 Connector API，并检查集合中的 PDF 覆盖情况。

## 仓库结构

```text
├── SKILL.md
├── README.md
├── scripts/
│   └── zotero_api.py
├── templates/
│   └── 筛选进度模板.md
├── DEPLOY_GUIDE.md
├── .gitignore
└── LICENSE
```

## 快速开始

### 前置条件

- Chrome + **Zotero Connector** 扩展
- **Zotero Desktop** 运行中（默认本地 Connector API 端口 23119）
- Web of Science 的合法访问权限
- Agent 模式需要支持 computer-use / 浏览器操控的 AI Agent

### 1. 测试 Zotero

```bash
python scripts/zotero_api.py ping
```

### 2. 检查 Zotero 集合

```bash
python scripts/zotero_api.py check -c "我的集合名"
```

### 3. 保存文献

```bash
python scripts/zotero_api.py save -i paper.json
```

`paper.json` 使用 Zotero Connector 翻译器格式，例如：

```json
{
  "itemType": "journalArticle",
  "title": "Example article title",
  "creators": [
    {"firstName": "Xin", "lastName": "Li", "creatorType": "author"}
  ],
  "DOI": "10.xxxx/example",
  "publicationTitle": "Example Journal",
  "date": "2026"
}
```

也可以从标准输入传入 JSON：

```bash
echo '{"items":[{"itemType":"journalArticle","title":"Example"}]}' | python scripts/zotero_api.py save
```

## Agent 使用方法

把 `SKILL.md` 放入你的 Agent 技能目录，然后告诉 Agent：

> 帮我从 WoS 搜集“XX 主题”的文献，筛选相关的存进 Zotero 的“XX”集合，能拿 PDF 就拿。

Agent 工作流包括：

**构建检索式 → 逐篇判断相关性 → Zotero 保存 → 三级 PDF 获取 → 进度记录 → 最终复核**

## PDF 获取策略

1. **EndNote Click / 页面可用 PDF**：等待 PDF 可用后，通过 Zotero Connector 保存。
2. **Publisher 页面**：进入出版商全文页面，再使用 Connector 保存。
3. **网页版 PDF**：进入 PDF 阅读页面后使用 Connector 保存。
4. **兜底**：无法获得全文时保存题录，并记录到无 PDF 清单。

PDF 获取受机构权限、出版商访问策略、Cloudflare/CAPTCHA 等因素影响，因此不能保证每篇文献都有 PDF。

## 安全与隐私

本仓库只保存通用 Agent 工作流和工具代码。个人 Zotero 数据库、实际筛选结果、文献标题清单等研究数据不应提交到公开仓库。

## License

MIT
