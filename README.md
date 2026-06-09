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
[![Version](https://img.shields.io/badge/version-v2.0-blue?style=for-the-badge)](https://github.com/nowa277/paper-reader/releases)

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
| **v2.0 决策驱动分析** | L1-L4 四级粒度输出：概念/关系/本体/证据图谱 |
| **三层质量验证** | L1 格式校验 / L2 内容校验 / L3 一致性校验 |
| **图像智能嵌入** | Base64 内联 / 外部文件 / Obsidian wikilink 三种策略 |
| **E2E 管道** | PDF → VLM → 分析 → 验证 → 嵌入，一键自动化 |
| **Subagent 并行管理** | 单 agent / Map-Reduce / Pipeline / ToT / Hierarchical 五种模式 |
| **跨平台** | 支持 Windows、macOS、Linux |

---

## 安装

### 推荐：直接告诉你的 AI Agent

```
请按照这个仓库的说明安装 paper-reader skill：https://github.com/nowa277/paper-reader
```

### 手动安装

```bash
# 克隆并本地安装
git clone https://github.com/nowa277/paper-reader.git
cd paper-reader
pip install -e .

# PyPI 安装（即将支持）
# pip install paper-reader
```

### Docker 安装（推荐用于服务器/云端）

```bash
# 克隆项目
git clone https://github.com/nowa277/paper-reader.git
cd paper-reader

# 构建镜像
docker build -t paper-reader .

# 运行
docker run -it --rm -v ~/papers:/app/papers paper-reader python main_skill.py --help

# 或使用 docker-compose
docker-compose up --build
```

### Docker + MinerU（PDF 转换功能）

```bash
# 使用 docker-compose 自动启动完整环境
docker-compose up paper-reader-mineru
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

### 分析论文 (v2.0 决策驱动)

```bash
/paper-reader analyze <paper-id>
```

v2.0 工作流：
1. **读** METHODOLOGY.md — 决策框架宪法
2. **答 4 问** — 文档类型 / 规模结构 / 用户意图 / 输出位置
3. **跑决策 prompt** — LLM 自动选择粒度、切分、图谱、输出策略
4. **调 API** — `analyze_with_decision()` 生成文件脚手架
5. **LLM 填内容** — Agent 完善分析结果

提示时选择分析级别（L1-L4）或使用 v1.0 兼容的 A/B/C 级

### 配置命令

```bash
/paper-reader setup mineru      # 检查 MinerU 状态
/paper-reader setup mineru install  # 安装 MinerU
/paper-reader setup config show  # 查看配置
```

---

## 分析级别 (v2.0)

| 级别 | 适用场景 | 输出内容 | Token 预算 |
|------|----------|----------|------------|
| **L1** | 快速浏览、概念速查 | 概念字典 | < 1k |
| **L2** | 深入阅读、用户指南 | 概念 + 关系图 | ~2-5k |
| **L3** | 知识库建设、教材 | 完整本体 (概念+关系+层级) | ~10-50k |
| **L4** | 科研准备、论文分析 | 完整图谱 (含证据引用) | ~50-200k |

> **v1.0 兼容**：A/B/C 级仍可用，分析器会自动向后兼容

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
│   ├── analyze/           # 论文分析 (v2.0 决策驱动)
│   │   ├── analyzer.py           # 核心 API (Decision, analyze_with_decision)
│   │   ├── METHODOLOGY.md        # v2.0 决策框架宪法
│   │   ├── decision_prompts/     # 4 个 LLM 决策 prompt
│   │   ├── granularity/          # L1-L4 档位定义
│   │   ├── subagent_policy.py    # Subagent 并行策略
│   │   ├── verification/         # L1/L2/L3 质量验证
│   │   ├── image_embedder.py    # 图像智能嵌入
│   │   └── e2e_integration.py   # 端到端管道
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
  "version": "2.0",
  "mineru": {
    "installed": false,
    "path": null
  },
  "fetch": {
    "default_mode": "jina"
  },
  "analyze": {
    "default_level": "L2",
    "enable_verification": true,
    "enable_image_embedding": false
  },
  "subagent": {
    "default_pattern": "SINGLE",
    "token_threshold_map_reduce": 50000,
    "token_threshold_hierarchical": 200000
  }
}
```

---

## License

MIT License
