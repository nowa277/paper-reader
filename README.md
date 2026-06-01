# Paper Reader Skill

<p align="center">
  <img src="https://img.shields.io/badge/Paper%20Reader-Skill-2563EB?style=for-the-badge&logo=book&logoColor=white" alt="Paper Reader">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge" alt="Python 3.10+">
</p>

<div align="center">

### 智能学术论文分析工具 | Intelligent Academic Paper Analysis Tool

**Search → Fetch → Analyze → Learn**

[![arXiv](https://img.shields.io/badge/arXiv-Search-orange?style=flat-square)](https://arxiv.org)
[![PubMed](https://img.shields.io/badge/PubMed-Search-blue?style=flat-square)](https://pubmed.ncbi.nlm.nih.gov)
[![Semantic Scholar](https://img.shields.io/badge/Semantic%20Scholar-Search-purple?style=flat-square)](https://semanticscholar.org)
[![MinerU](https://img.shields.io/badge/MinerU-PDF%20Conversion-red?style=flat-square)](https://github.com/opendatalab/MinerU)

</div>

---

## ✨ Features | 功能

| Feature | 功能 |
|:--------|------|
| 🔍 **Multi-Source Search** | 多源论文搜索 — arXiv、PubMed、Semantic Scholar、CrossRef |
| 📥 **Auto PDF Download** | 自动 PDF 下载，多源自动切换 |
| 🔄 **MinerU Integration** | PDF 转 Markdown，保留排版和图表 |
| 📊 **Multi-Level Analysis** | 三级分析 — 基础 / 学术 / 深度研究 |
| 🖥️ **Cross-Platform** | 跨平台支持 — Linux、macOS、Windows |

---

## 🚀 Quick Start | 快速开始

```bash
# 搜索论文 | Search papers
/paper-reader fetch "machine learning optimization"

/# 分析论文 | Analyze papers
/paper-reader analyze <paper-id>
```

### Installation | 安装

```bash
# 安装依赖 | Install dependencies
pip install requests psutil

# 安装 MinerU（可选 | optional）
paper-reader setup mineru install
```

---

## 📊 Analysis Levels | 分析级别

| Level | Description | 描述 |
|:------|-------------|------|
| 🅰️ **A** | Basic — Summary + Key Findings | 基础：摘要 + 关键发现 |
| 🅱️ **B** | Academic — + Methodology + Figures + Related Work | 学术：+ 方法论 + 图表 + 相关工作 |
| 🅲 **C** | Deep — + Limitations + Trends + Reproducibility | 深度：+ 局限性 + 趋势 + 复现分析 |

---

## 🏗️ Architecture | 架构

```
paper-reader/
├── skills/
│   ├── analyze/          # 论文分析 | Paper analysis
│   ├── config/          # 配置管理 | Configuration
│   ├── fetch/           # 论文获取 | Paper retrieval
│   │   └── sources/    # arXiv, PubMed, Semantic Scholar, CrossRef
│   └── mineru/          # PDF 解析 | PDF parsing
├── agent_adapters/       # Agent 适配器 | Agent adapters
└── tests/               # 测试套件 | Test suite
```

---

## 📄 License

MIT License
