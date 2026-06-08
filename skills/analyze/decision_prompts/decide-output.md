# Decision Prompt: Output Files & Location

## When
After Q4 存哪里 + 用户答完 output-questionnaire.md 的 3 件事后。

## Input Variables
- `{level}`: L1-L4
- `{use_case}`: 选自 output-questionnaire (obsidian / kb / transient / other)
- `{location}`: 用户指定的输出根目录
- `{doc_name}`: 文档名 (用于子目录)
- `{graph_decision}`: 来自 decide-graph 的完整 YAML

## Output Schema
```yaml
files: [string]  # 文件名列表 (相对 base_dir)
base_dir: string  # 完整输出路径
format: "wiki" | "md" | "json"
wikilinks: bool  # 仅 wiki 格式
cross_links: bool  # 是否生成 cross_links.md (跨文档关系)
reasoning: string
```

## Prompt

You are the paper-reader analyze subagent. Decide output file list and location.

**Reference**: METHODOLOGY.md §四 (L1-L4 输出文件) + §5.2 (输出衔接)

**Inputs**:
- level: {level}
- use_case: {use_case}
- location: {location}
- doc_name: {doc_name}
- graph_decision: {graph_decision}  # YAML 字符串

**Output** (YAML only):

```yaml
files: [<e.g. concepts.md, relations.md, hierarchy.md, evidence.md>]
base_dir: <{location}/{doc_name} 或用户指定>
format: <wiki|md|json>
wikilinks: <bool>
cross_links: <bool>
reasoning: |
  <为什么这些文件，引用 §四 L1-L4 定义>
```

## File Count by Level
- L1: `files = [concepts.md]` (1)
- L2: `files = [concepts.md, relations.md]` (2)
- L3: `files = [concepts.md, relations.md, hierarchy.md]` (3)
- L4: `files = [concepts.md, relations.md, hierarchy.md, evidence.md]` (4)

## Validation
- [ ] `files` 数量与 `level` 匹配 (L1=1, L2=2, L3=3, L4=4)
- [ ] `base_dir` 包含 `doc_name` 子目录
- [ ] `wikilinks=true` 必须 `format=wiki`
- [ ] `use_case=obsidian` → `format=wiki` + `wikilinks=true`
- [ ] `use_case=kb` → `format=md`（KB 通常 wiki 格式，但用户可指定）
- [ ] `use_case=transient` → `format=md` + `wikilinks=false`
- [ ] `level=L3|L4` + `use_case=obsidian` → `cross_links=true`（KB 需要链接）
- [ ] `base_dir` 路径必须**存在或可创建**（agent 自行 mkdir）

## Anti-patterns
- ❌ L1 输出 hierarchy.md（用户没要）
- ❌ L4 不输出 evidence.md（论文没证据等于没分析）
- ❌ use_case=obsidian 但 format=md → 用户看不到 wikilink
- ❌ base_dir 写到 `~/.paper-reader/` 而不问用户
- ❌ files 含相对路径（如 `output/concepts.md`）→ 应相对 base_dir
