# Level 3: 完整 ontology

## 何时用
参考 METHODOLOGY.md §三 Q1。

**典型场景**:
- 教材 / 教科书 (200-1000 页)
- 大型手册 (500+ 页, e.g. amber 1112 页)
- 用户问"建知识图"/"做 KB"
- amber-agent KB 长期使用

**Token 预算**: ~10-50k tokens (分块生成)

**必须分块**: L3 永远不能一次过。

## 核心提取内容
L2 全部 + 分类层级。

**层级关系**:
- `is_a`: A is_a B (A 是 B 的子类)
- `part_of`: A part_of B (A 是 B 的一部分)
- `taxonomy`: 树状分类

## 输出文件
- `concepts.md` (同 L1)
- `relations.md` (同 L2)
- `hierarchy.md` (新增)

### `hierarchy.md` 格式

```markdown
# <doc_name> 分类层级 (L3)

> 自动生成 by paper-reader analyze v2.0 | 档位: L3 | 日期: <date>

## 顶层分类 (root)

```yaml
- root: MD_Simulation
  children:
    - id: engines
      label: MD Engines
      children:
        - id: sander
          label: sander
        - id: pmemd
          label: pmemd
    - id: analysis
      label: Analysis Tools
      children:
        - id: cpptraj
          label: cpptraj
        - id: ptraj
          label: ptraj (deprecated)
    - id: prep
      label: Preparation
      children:
        - id: tleap
          label: tleap
        - id: xleap
          label: xleap
        - id: antechamber
          label: antechamber
```

## is_a 关系 (子类)

- [pmemd] is_a [md_engine] (§1.2)
- [sander] is_a [md_engine] (§1.1)
- [tleap] is_a [prep_tool] (§4.1)
- [cpptraj] is_a [analysis_tool] (§6.1)

## part_of 关系 (组成)

- [tleap] part_of [AMBER] (§4)
- [sander] part_of [AMBER] (§1)
- [prmtop] part_of [sander_input] (§1.5)

## 元信息
- 文档: <doc_name>
- 层级深度: <max depth, 通常 3-5>
- 根节点: <root name>
- 节点总数: <count>
```

## 决策要点

### ontology_style 选哪个
- `flat`: 1-2 层，只列顶层分类（适合 cheat sheet）
- `taxonomy`: 2-4 层，树状（适合教材/手册）⭐ 默认
- `deep`: 5+ 层，多维分类（适合大型 reference）

L3 默认 `taxonomy`。

### 分块策略
- 按章节切分（最常见）
- 每块独立生成 hierarchy 子树
- 最后 agent 合并去重 + 解决冲突（super-root 统一）

### 冲突解决
- 同一概念在不同块被分到不同父类 → 选最多块支持的
- 实在分不开 → 拆成两个节点，agent 标注 `[原: X, 重复]`
- 顶层根节点必须唯一（`MD_Simulation` 或用户指定）

## 反模式
- ❌ 层级深度 < 2 → 不够用
- ❌ 层级深度 > 6 → 难维护
- ❌ is_a 用错 (X is_a Y 但 Y 不是 X 的父类) → 知识错误
- ❌ 一次性生成不分块 → 必失败
- ❌ 分块生成的子树无法合并（ID 冲突 / 根节点多个）
- ❌ is_a + part_of 总数 < 概念数 / 4 → 漏提取

## 自检
- [ ] concepts.md + relations.md 完整 (同 L2 自检)
- [ ] hierarchy.md 至少 2 层
- [ ] 根节点 ≤ 1 (若有多个根, 用 super-root 统一)
- [ ] is_a + part_of 总数 ≥ 概念数 / 4
- [ ] 分块生成的子树可合并 (无 ID 冲突)
- [ ] YAML 格式合法 (用 `yaml.safe_load` 验证)
