# Level 2: 概念 + 关系

## 何时用
参考 METHODOLOGY.md §三 Q1。

**典型场景**:
- 用户指南 (10-200 页)
- 教程
- 用户问"概念之间怎么联系"
- amber-agent KB 初期建设

**Token 预算**: ~2-5k tokens 输出

## 核心提取内容
L1 全部 + 概念间关系。

**关系类型** (从 decide-graph 决策的 `relation_types` 字段):
- `contains`: A 包含 B (A 是集合, B 是元素)
- `uses`: A 使用 B (A 依赖 B 才能工作)
- `causes`: A 导致 B (因果)
- `is_a`: A 是 B 的子类
- `part_of`: A 是 B 的一部分
- `depends_on`: A 依赖 B
- `precedes`: A 先于 B (时序)

## 输出文件
- `concepts.md` (同 L1)
- `relations.md` (新增)

### `relations.md` 格式

```markdown
# <doc_name> 概念关系 (L2)

> 自动生成 by paper-reader analyze v2.0 | 档位: L2 | 日期: <date>

## 关系列表

### contains (包含)
- [AMBER] 包含 [sander] (§1.1)
- [AMBER] 包含 [pmemd] (§1.2)
- [sander] 包含 [energy_minimization] (§2.3)
...

### uses (使用)
- [pmemd] uses [cuda] (§1.2)
- [sander] uses [force_field] (§2.1)
...

### causes (导致)
- [high_temperature] causes [simulation_instability] (§5.4)
...

## 关系统计
- contains: 12
- uses: 8
- causes: 3
- 总关系数: 23

## 元信息
- 文档: <doc_name>
- 关系类型: <从 decide-graph 决策>
- 提取时间: <iso timestamp>
```

## 示例

**关系类型**: contains, uses

**输出**:
```markdown
### contains
- [sander] 包含 [min] (§2.1)
- [sander] 包含 [md] (§2.2)
- [pmemd] 包含 [min] (§3.1)
- [pmemd] 包含 [md] (§3.2)

### uses
- [sander] uses [prmtop] (§1.5)
- [pmemd] uses [prmtop] (§1.5)
- [sander] uses [inpcrd] (§1.5)
```

## 反模式
- ❌ 写 `related_to` 这种模糊关系 → 用具体类型
- ❌ 关系没章节定位 → 不可追溯
- ❌ 写无意义自环 (A 包含 A) → 跳过
- ❌ 关系总数 < 概念数 / 3 → 漏提取
- ❌ 概念没在 concepts.md 里出现（孤立概念）→ 关系悬空

## 自检
- [ ] concepts.md 完整 (同 L1 自检)
- [ ] relations.md 关系类型 ≥ 2
- [ ] 每个关系有 `[源] 关系 [目标] (§章节)` 格式
- [ ] 关系类型来自 decide-graph 决策（不是 agent 自己拍）
- [ ] 所有涉及的概念都在 concepts.md 里
- [ ] 关系总数 ≥ 概念数 × 0.3
