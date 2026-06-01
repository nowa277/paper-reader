# Paper Reader Skill

智能学术论文分析工具，支持 Claude Code 等 AI 编程 Agent。
An intelligent academic paper analysis tool for Claude Code and other AI coding agents.

---

## 功能 | Features

- **多源论文搜索 | Multi-Source Search** - 支持 arXiv、PubMed、Semantic Scholar、CrossRef
- **自动 PDF 下载 | Auto Download** - 从多个来源下载论文
- **MinerU 集成** - PDF 转 Markdown 用于分析
- **多级分析 | Multi-Level Analysis** - 三种分析级别（基础/学术/深度研究）
- **跨平台支持 | Cross-Platform** - 支持 Linux、macOS、Windows

## 安装 | Installation

```bash
# 安装依赖
pip install requests psutil

# 安装 MinerU（可选，用于 PDF 转换）
paper-reader setup mineru install
```

## 使用 | Usage

### 搜索论文 | Search Papers

```
/paper-reader fetch <topic-or-keywords>
```

### 分析论文 | Analyze Papers

```
/paper-reader analyze <paper-id>
```

### 分析级别 | Analysis Levels

| 级别 | 描述 | Level | Description |
|------|------|-------|-------------|
| A | 基础分析：摘要 + 关键发现 | A | Basic: Summary + Key Findings |
| B | 完整学术：+ 方法论 + 图表 + 相关工作 | B | Academic: + Methodology + Figures + Related Work |
| C | 深度研究：+ 局限性 + 趋势 + 复现分析 | C | Deep: + Limitations + Trends + Reproducibility |

## 架构 | Architecture

```
paper-reader/
├── skills/
│   ├── config/        # 配置管理 | Configuration
│   ├── mineru/        # MinerU PDF 解析
│   ├── fetch/         # 论文获取 | Paper retrieval
│   │   └── sources/   # arXiv, PubMed, Semantic Scholar, CrossRef
│   └── analyze/       # 论文分析 | Paper analysis
├── agent_adapters/    # Agent 适配器
├── docs/              # 设计文档
└── tests/             # 测试套件
```

## 配置 | Configuration

配置文件位于 `~/.paper-reader/config.json`。

## License

MIT
