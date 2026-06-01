# Paper Reader Skill - 局限性分析与改进日志

> 本文档记录 paper-reader skill 的已知局限性及其解决进度。
> 状态: 🔴 待处理 | 🟡 进行中 | ✅ 已解决

---

## 更新日志

| 日期 | 操作 | 描述 |
|------|------|------|
| 2026-06-01 | 更新 | P3 Q&A日志持久化完成 |
| 2026-06-01 | 更新 | Phase 2 完成：9个Agent适配器全部实现 |
| 2026-06-01 | 更新 | 根据 Phase 1 实现更新状态，将已解决问题移入 TODO 清单 |

---

## 一、系统与平台兼容性

### 已解决 ✅

| 问题 | 解决方案 | 状态 |
|------|----------|------|
| **路径硬编码** | ✅ Phase 1 已实现 `config_manager.py`，支持 `~/.paper-reader/config.json` 配置 | ✅ |
| **HOME 变量依赖** | ✅ 配置系统支持自定义路径，通过 `config.json` 管理 | ✅ |
| **Linux 专有** | ✅ Phase 1 已实现跨平台检测 (`platform.py`)，支持 Linux/macOS/Windows | ✅ |
| **macOS 兼容性存疑** | ✅ 已添加 macOS 版本检测、Homebrew 路径检测 | ✅ |
| **WSL 边界情况** | ✅ 已添加 WSL 版本检测 (WSL1/WSL2) | ✅ |
| **Windows 兼容性** | ✅ 已添加 Windows Shell 检测 (PowerShell/CMD) | ✅ |

---

### 待处理 🔴

| 局限性 | 详细说明 | 优先级 |
| ------ | -------- | ------ |
| **Python 版本要求** | 未说明最低版本要求 (建议 3.8+) | P2 |
| **虚拟环境兼容** | venv vs conda vs uv 需要进一步测试 | P2 |
| **系统依赖** | curl, pandoc, tesseract 等外部工具检测缺失 | P1 |

---

## 二、外部依赖与服务

### 已解决 ✅

| 问题 | 解决方案 | 状态 |
|------|----------|------|
| **MinerU 需预先安装** | ✅ Phase 1 已实现 `detector.py` 自动检测 + `installer.py` 自动安装 | ✅ |
| **无配置管理** | ✅ Phase 1 已实现 `config_manager.py` + `config.json` | ✅ |
| **路径不一致** | ✅ 统一配置在 `~/.paper-reader/config.json` | ✅ |

---

### 待处理 🔴

| 局限性 | 详细说明 | 优先级 |
| ------ | -------- | ------ |
| **Jina Reader API 限速** | 免费版 20 RPM 限速，需要添加速率控制 | P1 |
| **网络依赖** | 依赖外网访问，国内可能需要代理配置 | P2 |
| **web_search 工具依赖** | 依赖 MCP 工具，非所有环境都配备 | P2 |
| **vision_analyze 依赖** | 模型无视觉能力时需明确 fallback 策略 | P2 |

---

## 三、功能性局限

### 已解决 ✅

| 问题 | 解决方案 | 状态 |
|------|----------|------|
| **Claude Code 简化版功能缺失** | ✅ Phase 1 已完善 SKILL.md，与完整版一致 | ✅ |
| **多副本维护困难** | ✅ 统一为单一数据源 `~/.paper-reader/config.json` | ✅ |

---

### 待处理 🔴

| 局限性 | 详细说明 | 优先级 |
| ------ | -------- | ------ |
| **硬付费墙无法突破** | Cell, NEJM, JAMA 等顶级期刊只能获取元数据 | P3 |
| **arXiv 摘要URL处理** | 需要手动添加 `/pdf/` 后缀 | P2 |
| **图像识别依赖模型能力** | 无 vision 时 figures 分析降级 | P2 |
| **非英语论文支持** | MinerU `-l ch` 支持有限 | P2 |
| **大型PDF性能** | 200+ 页无并行处理机制 | P2 |
| **多语言文档与代码不匹配** | 6语言 README，代码无国际化 | P3 |

---

## 四、Agent 适配性问题

### 已解决 ✅

| Agent | 之前 | 现在 | 状态 |
|-------|------|------|------|
| **Claude Code** | ⚠️ 简化版 | ✅ 完整 SKILL.md | ✅ |
| **Cursor** | ❌ 无适配 | ✅ cursor_rules.j2 模板 | ✅ |
| **Windsurf** | ❌ 无适配 | ✅ generate_skill_file 实现 | ✅ |
| **Zed** | ❌ 无适配 | ✅ zed_md.j2 模板 | ✅ |
| **Copilot CLI** | ❌ 无适配 | ✅ generate_skill_file 实现 | ✅ |
| **Gemini CLI** | ❌ 无适配 | ✅ generate_skill_file 实现 | ✅ |
| **Hermes (agentskills.io)** | ❌ 无适配 | ✅ hermes_yaml.j2 模板 | ✅ |
| **OpenCode** | ❌ 无适配 | ✅ opencode_json.j2 模板 | ✅ |
| **Codex** | ❌ 无适配 | ✅ generate_skill_file 实现 | ✅ |

---

## 五、错误处理与鲁棒性

### 待处理 🔴

| 场景 | 当前处理 | 改进方向 | 优先级 |
|------|----------|----------|--------|
| **MinerU 失败** | 提示"检查文件完整性" | 添加重试机制和详细错误日志 | P1 |
| **Jina Reader 超时** | 30s 超时 | 添加可配置超时和用户反馈 | P2 |
| **PDF 损坏** | 提示"不是PDF文件" | 尝试提取可用部分 | P2 |
| **磁盘空间不足** | 无检查 | 添加预检查 | P2 |
| **网络中断** | 无断点续传 | 添加下载恢复 | P1 |
| **归档目录不存在** | 无自动创建 | 自动创建目录 | P1 |

---

## 六、性能与资源

### 待处理 🔴

| 指标 | 问题 | 改进方向 | 优先级 |
|------|------|----------|--------|
| **MinerU 串行** | 严格禁止并行 | 评估是否可并行 | P2 |
| **内存占用** | 未提及 | 大型 PDF 添加 OOM 保护 | P2 |
| **临时文件清理** | 无自动清理 | 添加自动清理机制 | P2 |
| **缓存机制** | 无 | 添加论文缓存 | P2 |

---

## 七、用户体验

### 待处理 🔴

| 问题 | 改进方向 | 优先级 |
|------|----------|--------|
| **交互流程长 (6步)** | 简化流程 | P2 |
| **无进度条** | 添加 MinerU 进度反馈 | P1 |
| **领域检测可能不准** | 改进检测算法 | P2 |
| **无撤销机制** | 添加操作撤销 | P3 |
| **Q&A 模式未持久化** | 添加日志持久化 | P3 |
| **批量模式风险高** | 添加检查点机制 | P1 |

---

## 八、维护与扩展性

### 待处理 🔴

| 问题 | 改进方向 | 优先级 |
|------|----------|--------|
| **领域扩展困难** | 模块化领域模板 | P2 |
| **模板修改复杂** | 分离模板与代码 | P2 |
| **无单元测试** | 添加完整测试套件 | P1 |
| **无版本管理** | 添加版本回退 | P3 |
| **文档与代码不同步** | 自动化文档检查 | P2 |

---

## 九、法律与伦理

### 待处理 🔴

| 问题 | 说明 | 优先级 |
|------|------|--------|
| **版权灰色地带** | 批量下载可能涉及版权 | P3 |
| **Jina Reader 使用条款** | 免费版有使用限制 | P3 |
| **数据隐私** | 论文上传至第三方服务 | P2 |

---

## TODO 清单 (按优先级排序)

### 🔴 P0 - 紧急

- [ ] 添加系统依赖检测 (curl, pandoc, tesseract)
- [ ] 添加完整单元测试套件

### 🟠 P1 - 高优先级

- [ ] 添加 Jina Reader API 速率控制
- [ ] 添加网络中断断点续传
- [ ] 自动创建归档目录
- [ ] 添加 MinerU 长时间运行进度条
- [ ] 添加批量处理检查点机制

### 🟡 P2 - 中优先级

- [ ] 添加 Python 版本要求检测
- [ ] 添加虚拟环境兼容性测试
- [ ] 添加磁盘空间预检查
- [ ] 改进大型 PDF 并行处理评估
- [ ] 添加临时文件自动清理
- [ ] 添加论文缓存机制
- [ ] 简化交互流程

### 🟢 P3 - 低优先级

- [x] 新增 Agent 适配器模板 (Cursor, Windsurf, Zed, etc.) ✅
- [x] 添加 Q&A 日志持久化 ✅
- [ ] 添加版本管理/回退功能
- [ ] 添加操作撤销机制
- [ ] 文档与代码同步检查

---

## Phase 1 完成总结

**完成日期:** 2026-06-01

**已实现功能:**

1. ✅ **平台检测系统** (`paper-reader/skills/config/platform.py`)
   - `PlatformInfo` dataclass
   - Linux 发行版检测 (Ubuntu/Debian/RedHat)
   - WSL 版本检测 (WSL1/WSL2)
   - macOS 版本检测
   - Windows Shell 检测 (PowerShell/CMD)
   - 向后兼容包装函数

2. ✅ **MinerU 管理** (`paper-reader/skills/mineru/`)
   - `detector.py` - 自动检测 MinerU
   - `installer.py` - 自动安装 MinerU
   - 完整测试覆盖

3. ✅ **配置管理** (`paper-reader/skills/config/config_manager.py`)
   - JSON 配置存储在 `~/.paper-reader/config.json`
   - 支持获取/设置配置项
   - 默认配置自动创��

4. ✅ **分层子技能架构**
   - `skills/config/` - 配置子技能
   - `skills/mineru/` - MinerU 子技能
   - `skills/fetch/` - 获取子技能 (框架)
   - `skills/analyze/` - 分析子技能 (框架)

5. ✅ **文档完善**
   - 完整 SKILL.md
   - 设计文档 (`docs/superpowers/specs/`)
   - 实现计划 (`docs/superpowers/plans/`)

---

## Phase 2 完成总结

**完成日期:** 2026-06-01

**已实现功能:**

1. ✅ **Agent 适配器架构**
   - `agent_adapters/base.py` - BaseAdapter 抽象基类 + AdapterConfig 数据类
   - `agent_adapters/registry.py` - Registry 注册中心模式
   - `agent_adapters/generator.py` - Generator 基于 Jinja2 模板生成文件

2. ✅ **9个Agent适配器全部实现**
   - ClaudeAdapter - Claude Code
   - HermesAdapter - agentskills.io (YAML格式)
   - CodexAdapter - OpenAI Codex
   - OpenCodeAdapter - OpenCode (JSON格式)
   - CursorAdapter - Cursor (cursor_rules.j2)
   - WindsurfAdapter - Windsurf
   - ZedAdapter - Zed (zed_md.j2)
   - CopilotAdapter - GitHub Copilot CLI
   - GeminiAdapter - Google Gemini CLI

3. ✅ **Jinja2 模板系统**
   - `templates/skill_md.j2` - 通用技能Markdown
   - `templates/agents_md.j2` - Agent列表
   - `templates/hermes_yaml.j2` - Hermes YAML格式
   - `templates/opencode_json.j2` - OpenCode JSON格式
   - `templates/cursor_rules.j2` - Cursor规则
   - `templates/zed_md.j2` - Zed Markdown

4. ✅ **代码审查修复**
   - HermesAdapter 使用模板处理 skill_source 参数
   - 所有适配器 import json 移至模块级别
   - 添加适当的文档字符串

---

*本文档将持续更新，记录每个局限性的解决进度。*