# Paper Reader Skill 详解文档

> 作者: Sesley Cheung | 版本: v1.0.0 | License: MIT

---

## 一、整体架构概览

### 1.1 核心设计理念

Paper Reader 是一个基于 MinerU 的学术论文分析 skill，支持：
- **多源论文获取**: 本地PDF / URL / arXiv ID / DOI
- **领域感知分析**: 5大专业领域定制化检查清单
- **多种阅读模式**: 快速筛选 / 深度精读 / 问答交互 / 批量处理
- **Obsidian 归档**: 结构化笔记 + YAML frontmatter

### 1.2 5阶段处理流水线

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Paper Reader Pipeline                         │
│                                                                      │
│  ┌─────────┐   ┌──────────┐   ┌──��───────┐   ┌────────┐   ┌──────┐ │
│  │ Stage 1 │──▶│ Stage 2  │──▶│ Stage 3  │──▶│ Stage 4│──▶│Stage5│ │
│  ��  Fetch  │   │  Detect  │   │  Select  │   │Execute │   │Output│ │
│  └─────────┘   └──────────┘   └──────────┘   └────────┘   └──────┘ │
│       │                                              │              │
│  ┌────┴──────────────────────────┐          ┌───────┴───────┐      │
│  │ 3-Tier Content Acquisition   │          │  Domain       │      │
│  │ ① Jina Reader  (1-2s)       │          │  Checklists   │      │
│  │ ② Direct Download (arXiv)   │          │  · MD / Med   │      │
│  │ ③ web_search    (2-5s)      │          │  · AI / Bio   │      │
│  └──────────────────────────────┘          │  · Prog       │      │
│                                             └───────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、文件结构

```
paper-reader/
├── SKILL.md                    # 核心skill定义 (312行)
├── README.md                   # 英文文档
├── LICENSE                     # MIT License
├── package.json                # npm元数据
├── .gitignore
├── adapters/                   # 多Agent适配器
│   ├── README.md
│   ├── claude-code/
│   │   └── commands/
│   │       └── paper-reader.md # Claude Code命令
│   ├── codex/
│   │   └── AGENTS.md           # Codex配置
│   └── opencode/
│       └── agent-config.json   # OpenCode配置
├── scripts/                    # 辅助脚本
│   ├── extract.sh              # MinerU封装 (bash)
│   └── fetch_paper.py          # 统一获取器 (Python)
└── references/                 # 领域清单与模式指南
    ├── archive-template.md     # Obsidian笔记模板
    ├── domain-ai-ml.md         # AI/ML领域清单 (12字段)
    ├── domain-bioinformatics.md # 生物信息学 (11字段)
    ├── domain-medicine.md      # 医学领域 (12字段)
    ├── domain-molecular-dynamics.md # 分子动力学 (16字段)
    ├── domain-programming.md   # 编程领域 (10字段)
    ├── mineru-quirks.md        # MinerU注意事项
    ├── mode-batch.md           # 批量处理模式
    ├── mode-deep.md            # 深度精读模式
    ├── mode-qa.md              # 问答交互模式
    └── mode-scan.md            # 快速筛选模式
```

---

## 三、核心流程详解

### 3.1 触发条件

| 触发类型 | 示例 | 处理方式 |
|---------|------|---------|
| 中文指令 | "读论文", "分析论文", "帮我看看这篇" | 直接激活 |
| 英文指令 | "read this paper", "analyze PDF" | 直接激活 |
| 本地文件 | `/path/to/paper.pdf` | 验证后直接MinerU |
| arXiv ID | `2402.03300` | 自动构造URL |
| arXiv URL | `arxiv.org/pdf/...` | Tier 1/2/3 降级 |
| DOI | `10.1038/s42256-026-01223-x` | 优先Jina Reader |
| 批量 | "Paper Alert", 多URL列表 | 启用batch模式 |

### 3.2 内容获取策略 (3-Tier)

**统一工具**: `python3 $FETCH_SCRIPT <url> --output-dir <dir>`

| 优先级 | 方法 | 适用场景 | 质��� |
|--------|------|---------|------|
| **Tier 1** | Jina Reader (`r.jina.ai`) | arXiv, bioRxiv, 开放获取 | ⭐⭐⭐⭐⭐ 直接Markdown |
| **Tier 2** | `curl -L` 直接下载 | arXiv PDF | ⭐⭐⭐⭐ PDF需MinerU |
| **Tier 3** | web_search | Nature, Elsevier, 付费 | ⭐⭐ 元数据+摘要 |

**Jina Reader 关键优势**:
- 绕过 Cloudflare 机器人检测
- 直接输出 Markdown (1-2秒)
- arXiv/bioRxiv 近乎100%成功率

**速率限制**: 免费版 20 RPM

### 3.3 领域检测

**快速扫描**: 提取前3页内容

**关键词匹配**:

| 领域ID | 领域名称 | 关键词 |
|--------|---------|--------|
| `md` | 分子动力学 | molecular dynamics, force field, GROMACS, AMBER, RMSD, free energy, trajectory, docking |
| `med` | 医学 | clinical trial, randomized, cohort, patients, treatment, placebo, hazard ratio, RCT, prognosis |
| `ai` | AI/ML | neural network, deep learning, transformer, training, benchmark, SOTA, accuracy, LLM |
| `bio` | 生物信息学 | RNA-seq, genome, GWAS, gene expression, variant calling, differential expression |
| `prog` | 编程 | compiler, operating system, database, algorithm, system design, performance, runtime |

**用户确认流程**:
```
检测到论文领域: {domain_name} ({confidence})
标题: {detected_title}

确认领域:
  A. ✅ 正确
  B. 🔄 我选择其他领域
```

### 3.4 分析模式选择

| 模式 | 描述 | 耗时 | 归档 |
|------|------|------|------|
| A. 快速筛选 | 3分钟概览，判断是否值得精读 | ~3min | ❌ |
| B. 深度精读 | 全文结构化拆解 + Obsidian归档 | ~10-15min | ✅ |
| C. 问答阅读 | 交互问答模式 | 不限 | 可选 |
| D. 批量处理 | 批量论文并行处理 | 视数量 | ✅ |

---

## 四、领域检查清单详情

### 4.1 分子动力学 (MD) - 16字段
```
simulation_system, force_field, water_model, box_type_size,
ions, equilibration_protocol, production_time, timestep,
software, hardware, free_energy_methods, enhanced_sampling,
analysis_metrics, key_parameters, limitations, reproducibility
```

### 4.2 医学 (Medicine) - 12字段
```
study_design, sample_size, population, intervention, control,
primary_endpoint, statistical_methods, effect_size, adverse_events,
reporting_standards, evidence_level, clinical_relevance
```

### 4.3 AI/ML - 12字段
```
task_type, model_architecture, pretraining_data, training_data,
hyperparameters, benchmark, sota_comparison, evaluation_metrics,
ablations, compute_resources, reproducibility, limitations
```

### 4.4 生物信息学 - 11字段
```
analysis_type, species, sample_size, data_source, alignment_tool,
differential_analysis_tool, statistical_thresholds, functional_enrichment,
validation_methods, reproducibility, key_genes_variants
```

### 4.5 编程 - 10字段
```
system_type, core_algorithm, programming_language, system_scale,
performance_metrics, benchmarks, experimental_environment,
code_availability, practical_value
```

---

## 五、关键脚本说明

### 5.1 extract.sh (MinerU封装)

```bash
#!/bin/bash
# 用法: extract.sh <pdf_path> <output_dir> [lang] [start_page] [end_page]

# 示例:
# extract.sh /path/to/paper.pdf /tmp/output en 0 10
```

**功能**:
- 验证PDF文件存在性和类型
- 支持语言参数 (`-l en` / `-l ch`)
- 支持页码范围 (`-s 0 -e 3`)
- 报告输出文件列表

### 5.2 fetch_paper.py (统一获取器)

```python
# 用法: python3 fetch_paper.py <url> --output-dir <dir>

# 支持:
# - arXiv ID: 2402.03300
# - arXiv URL: https://arxiv.org/pdf/...
# - DOI: 10.1038/...
# - 任意URL
```

**策略**:
1. 尝试 Jina Reader (Tier 1)
2. 失败则尝试直接下载 (Tier 2)
3. 再失败则 web_search (Tier 3)

---

## 六、MinerU 注意事项

详见 `references/mineru-quirks.md`

**关键点**:
- 语言参数必须指定: `-l en` 或 `-l ch`，不支持 `-l auto`
- 大文件 (>200页) 自动分段
- 输出结构: `{output_dir}/{part}/auto/*.md`
- 页码范围 quirk: `-s 0 -e 3` 实际处理4页
- 严格串行执行，禁止并行MinerU进程

---

## 七、多Agent适配

| Agent | 配置位置 | 功能 |
|-------|---------|------|
| Claude Code | `adapters/claude-code/commands/paper-reader.md` | `/paper-reader` 命令 |
| Codex | `adapters/codex/AGENTS.md` | 项目级AGENTS.md |
| OpenCode | `adapters/opencode/agent-config.json` | JSON配置 |
| Hermes/通用 | `SKILL.md` | 完整skill定义 |

**适配器状态表**:

| 特性 | Claude Code | Codex | OpenCode |
|------|-------------|-------|----------|
| 触发词 | /paper-reader | 上下文 | 配置 |
| 批量模式 | ✅ | ✅ | ✅ |
| 归档 | ✅ | ✅ | ✅ |
| Q&A模式 | ✅ | ✅ | ✅ |

---

## 八、已知局限性

1. **硬付费墙无法突破**: Cell, NEJM, JAMA 等
2. **arXiv摘要URL需转换**: 需添加 `/pdf/` 后缀
3. **MinerU严格串行**: 无法并行处理多论文
4. **Jina Reader限速**: 免费版20 RPM
5. **视觉分析依赖模型**: GLM-5.1等模型无vision能力
6. **大型PDF性能**: 200+页需要分段处理

---

## 九、环境变量配置

```bash
MINERU="/home/user/.hermes/hermes-agent/venv/bin/mineru"
WORK_BASE="/tmp/paper-reader"
ARCHIVE_BASE="$HOME/obsidian/papers"
EXTRACT_SCRIPT="$HOME/.hermes/skills/paper-reader/scripts/extract.sh"
JINA_READER="https://r.jina.ai"
FETCH_SCRIPT="$HOME/.hermes/skills/paper-reader/scripts/fetch_paper.py"
```

---

## 十、归档格式

**Obsidian 笔记结构**:
```yaml
---
title: {paper_title}
date: {YYYY-MM-DD}
domain: {domain_id}
tags: [{domain}, {tags}]
rating: {1-5}
authors: [{authors}]
year: {YYYY}
doi: {doi}
---

# 论文基本信息

# 核心贡献

# 方法概述

# 实验结果

# 关键图表

# 优缺点分析

# 相关工作

# 引用建议
```

**目录结构**:
```
~/obsidian/papers/
├── molecular-dynamics/
│   ├── 2026-AlphaFold3-MD-Simulations.md
│   └── images/
│       ├── fig1_rmsd_plot.jpg
│       └── ...
├── medicine/
├── ai-ml/
├── bioinformatics/
└── programming/
```

---

## 十一、多语言文档

| 文件 | 语言 |
|------|------|
| `README.md` | English |
| `docs/README.zh-CN.md` | 简体中文 |
| `docs/README.zh-TW.md` | 繁體中文 |
| `docs/README.ja.md` | 日本語 |
| `docs/README.es.md` | Español |
| `docs/README.ru.md` | Русский |

---

## 十二、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0.0 | 2026 | 初始发布，支持5大领域+4种模式 |