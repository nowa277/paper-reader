<!--
╔══════════════════════════════════════════════════════════════════════╗
║  DreamSeed 种梦计划 — AI创造者大赛  官方 README 模板                ║
║                                                                      ║
║  使用说明：                                                          ║
║  1. 将本模板放在参赛仓库根目录 README.md 的顶部                       ║
║  2. 头图使用 DreamField 官方公开活动图片地址                         ║
║  3. 请保留 DREAMFIELD_README_HEADER_START / END 标识                 ║
║  4. 分割线以下供创作者自由编写项目内容                               ║
╚══════════════════════════════════════════════════════════════════════╝
-->

<!-- DREAMFIELD_README_HEADER_START -->

<p align="center">
  <a href="https://www.dreamfield.top">
    <img src="https://www.dreamfield.top/dream-field/contest-readme/assets/dreamseed-readme-banner.png" alt="DreamSeed 种梦计划参赛作品" width="100%" />
  </a>
</p>

<!-- DREAMFIELD_README_HEADER_END -->

<div align="center">

# Paper Reader

### 智能学术论文分析工具，支持 Claude Code 等 AI 编程 Agent

**Search · Fetch · Analyze · Learn**

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&color=2ea44f)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Version](https://img.shields.io/badge/version-v1.10.1-blue?style=for-the-badge)](https://github.com/nowa277/paper-reader/releases)

[![Windows](https://img.shields.io/badge/Windows-Supported-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#supported-platforms)
[![macOS](https://img.shields.io/badge/macOS-Supported-A2AAAD?style=for-the-badge&logo=apple&logoColor=white)](#supported-platforms)
[![Linux](https://img.shields.io/badge/Linux-Supported-FCC434?style=for-the-badge&logo=linux&logoColor=black)](#supported-platforms)

[![arXiv](https://img.shields.io/badge/arXiv-Search-orange?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org)
[![PubMed](https://img.shields.io/badge/PubMed-Search-0099CC?style=flat-square)](https://pubmed.ncbi.nlm.nih.gov)
[![Semantic Scholar](https://img.shields.io/badge/Semantic%20Scholar-Search-8C4A8D?style=flat-square)](https://semanticscholar.org)
[![MinerU](https://img.shields.io/badge/MinerU-PDF%20Conversion-red?style=flat-square)](https://github.com/opendatalab/MinerU)

[![Claude Code](https://img.shields.io/badge/Claude_Code-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Cursor](https://img.shields.io/badge/Cursor-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Codex](https://img.shields.io/badge/Codex-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![opencode](https://img.shields.io/badge/opencode-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Copilot](https://img.shields.io/badge/Copilot-Supported-8B5CF6?style=flat-square)](#supported-agents)

[**简体中文**](README.md) · [**English**](README_CN.md)

![Paper Reader Hero Banner](hero-banner.png)

</div>

---

## 概述

Paper Reader 是一款面向 AI 编程 Agent 的智能学术论文分析工具。它提供从论文检索到深度分析的完整工作流，支持多个学术数据库并输出结构化的 Markdown 内容。

**适用场景：**
- 科研文献调研与综述
- 快速筛选相关论文
- 深入分析研究方法和结论
- 跟踪研究趋势与空白
- 学术写作准备

---

## 主要功能

| 功能 | 描述 |
|------|------|
| **多源搜索** | 同时在 arXiv、PubMed、Semantic Scholar、CrossRef 搜索论文 |
| **自动下载** | 多源自动切换下载论文 PDF |
| **MinerU 集成** | PDF 转 Markdown，保留排版、图表和表格 |
| **多级分析** | 三种分析级别：基础、学术、深度研究 |
| **跨平台** | 支持 Windows、macOS、Linux |

---

## 安装

```bash
# 手动安装
pip install paper-reader
pipx install paper-reader
```
当然也可以直接告诉你的agent
```bash
Please follow the instructions in this repository: https://github.com/nowa277/paper-reader to configure and install the skill.
```

**依赖**
- Python 3.10+
- `requests` 和 `psutil`（自动安装）

**可选**：如需 PDF 转 Markdown 功能，请自行安装 [MinerU](https://github.com/opendatalab/MinerU)。

---

## 快速开始

### 搜索论文

```bash
/paper-reader fetch "machine learning optimization"
```

Agent 会在多个学术数据库搜索，返回相关论文列表及元数据（标题、作者、年份、摘要、来源）。

### 分析论文

```bash
/paper-reader analyze <paper-id>
```

提示时选择分析级别：
- **A级** — 基础：摘要 + 关键发现
- **B级** — 学术：+ 方法论 + 图表 + 相关工作
- **C级** — 深度：+ 局限性 + 趋势 + 复现分析

### 配置命令

```bash
/paper-reader setup mineru      # 检查 MinerU 状态
/paper-reader setup mineru install  # 安装 MinerU
/paper-reader setup config show  # 查看配置
```

---

## 分析级别

| 级别 | 适用场景 | 输出内容 |
|------|----------|----------|
| **A** | 快速浏览、概览 | 摘要、关键发现、一段式总结 |
| **B** | 深入阅读 | 完整摘要、方法论、图表、相关工作对比 |
| **C** | 科研准备 | 批判性分析、局限性、趋势、可复现性评估 |

---

## 多源搜索

| 来源 | 擅长领域 |
|------|----------|
| **arXiv** | 计算机科学、物理、数学、金融工程 |
| **PubMed** | 生物医学、生命科学、医学 |
| **Semantic Scholar** | 广泛覆盖、引用图谱、AI 推荐 |
| **CrossRef** | DOI 查询、出版商元数据 |

---

## 支持的平台

| 平台 | 状态 |
|------|------|
| Linux | 支持 |
| macOS | 支持 |
| Windows | 支持 |

---

## 支持的 Agent

| Agent | 状态 |
|-------|------|
| Claude Code | 支持 |
| Cursor | 支持 |
| Codex CLI | 支持 |
| opencode | 支持 |
| Hermes Agent | 支持 |
| Gemini CLI | 支持 |
| Copilot | 支持 |
| Windsurf | 支持 |
| Zed | 支持 |

---

## 架构

```
paper-reader/
├── skills/
│   ├── analyze/           # 多级论文分析输出
│   ├── config/            # 配置管理
│   ├── fetch/             # 论文检索与搜索
│   │   └── sources/      # arXiv、PubMed、Semantic Scholar、CrossRef
│   └── mineru/            # PDF 转 Markdown
├── agent_adapters/         # Agent 适配器实现
└── tests/                 # 测试套件
```

---

## 配置

配置文件：`~/.paper-reader/config.json`

```json
{
  "version": "1.0",
  "mineru": {
    "installed": false,
    "path": null
  },
  "fetch": {
    "default_mode": "jina"
  },
  "analyze": {
    "default_template": "default"
  }
}
```

---

## License

MIT License
