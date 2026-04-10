# 组装规则 — 各章节详细组装逻辑

本文件定义 Compile 命令在组装 SKILL.md 各章节时的详细规则。

---

## 1. 章节映射表

| 序号 | SKILL.md 章节 | 知识文档来源 | 组装方式 |
|------|--------------|-------------|---------|
| 1 | YAML 前置元数据 | 元数据头 + Iron Rules | 生成 |
| 2 | 标题 + 概述 | `one_liner` + `domain` | 生成 |
| 3 | 工具调用 | Tool Interface + 适配器 | 模板填充 |
| 4 | 硬性规则 | Iron Rules | 直接复制 |
| 5 | 语义理解 | Semantic Framework | 直接复制 |
| 6 | 请求格式规范 | Request Specification | 直接复制 |
| 7 | 构建流程 | 骨架模板 + 各章节 | 自动组装 |
| 8 | 输出展示规范 | Output Specification | 直接复制 |
| 9 | 完整示例 | Examples | 直接复制 |
| 10 | 常见错误模式 | Error Patterns | 直接复制 |

---

## 2. 各组装方式详解

### 2.1 "直接复制" 章节

直接复制意味着从知识文档原封不动搬入 SKILL.md，但需做以下微调：

1. **标题层级调整**：知识文档中 `##` 在 SKILL.md 中可能需要调整为 `###`（根据最终嵌套层级）
2. **内部链接更新**：如果章节间有交叉引用，更新为 SKILL.md 内的锚点
3. **添加引导语**：在章节开头添加一句话说明上下文

示例：
```markdown
## 硬性规则

> 构建任何请求前，务必逐条过一遍以下规则：

{从知识文档 Iron Rules 章节直接复制的内容}
```

### 2.2 "模板填充" 章节

仅工具调用章节使用此方式。流程：

```
1. 从知识文档读取工具列表及其参数定义
2. 从当前环境的适配器读取调用方式模板
3. 对每个工具：
   a. 用工具名替换模板中的 {tool_name}
   b. 用参数列表替换模板中的 {params}
   c. 用工具描述替换模板中的 {description}
   d. 附上调用示例和返回格式
```

如果知识文档的 Tool Interface 中有 `mcp_server` 字段：
- Cursor → 使用 CallMcpTool 模板
- Claude Code → 生成 `mcp__server__tool` 调用格式
- AI Portal → 使用内置函数调用模板

如果知识文档的 Tool Interface 中有 `http_endpoint` 字段：
- 所有环境 → 使用 curl/HTTP 调用模板
- 差异仅在认证方式（环境变量 vs 配置文件 vs 平台自动）

### 2.3 "生成" 章节

YAML 元数据和标题需要根据知识文档内容自动生成。

**YAML 元数据生成规则**：

```yaml
---
name: {domain_slug}
description: |
  {WHAT}: {one_liner}。通过 {tool_list} 工具{核心动作}。
  {WHEN}: 当用户{触发场景}时使用本 skill。
  关键词: {从典型用户表达中提取 5-10 个关键词}
  {EMPHASIS}: {从 Iron Rules 中提取最重要 1-2 条作为前置警告}
---
```

各字段来源：
- `domain_slug`：知识文档元数据 `domain_slug`
- `one_liner`：知识文档元数据 `one_liner`
- `tool_list`：知识文档 `## Tool Interface` 中所有工具的 `display_name`
- `核心动作`：知识文档 `## Domain Overview` → Purpose
- `触发场景`：知识文档 `## Domain Overview` → Typical Expressions
- `关键词`：从 Typical Expressions 提取名词和动词
- `EMPHASIS`：Iron Rules 中标记为最高优先级的规则

### 2.4 "自动组装" 章节

仅构建流程使用此方式。详见 [skeleton-template.md](skeleton-template.md)。

---

## 3. 拆分触发与执行

### 触发条件

组装完成后计算总行数（`wc -l`），如果 > 500 行则触发拆分。

### 拆分执行

```
phase_1: 计算各章节行数
  sections = {
    "工具调用": N1,
    "硬性规则": N2,
    "语义理解": N3,
    ...
  }

phase_2: 按优先级移出章节
  可移出清单（按优先级排序，先移走最不紧急的）:
    1. 完整示例 → references/examples.md
    2. 常见错误模式 → references/error-patterns.md
    3. 详细参数规范 → references/param-spec.md
    4. 语义理解（如仍超）→ references/semantic-framework.md

  不可移出（必须留在 SKILL.md）:
    - YAML 元数据 + 概述
    - 工具调用
    - 硬性规则
    - 构建流程 + 自检清单
    - 输出展示规范

phase_3: 替换移出的章节为引用
  对每个被移出的章节:
    在 SKILL.md 中替换为:
      "详见 [文件名](references/文件名)"
```

### 移出章节格式

被移出到 references/ 的每个文件应包含：

```markdown
# {章节标题}

> 本文件是 {domain} skill 的参考文件，由 Compile 命令自动生成。
> 主文件: ../SKILL.md

{章节原始内容}
```

---

## 4. 格式规范

### JSON 示例中的转义

知识文档中的 JSON 示例可能包含未转义的双引号。组装时检查并修正：

```
原始: "filter": "store_name == "上海新天地""
修正: "filter": "store_name == \"上海新天地\""
```

### Markdown 格式

- 代码块使用 ``` 包裹，标注语言（json/bash/yaml）
- 表格使用标准 Markdown 表格语法，对齐竖线
- 列表使用 `-` 而非 `*`

### 行宽

- 表格行不做强制换行
- 其他文本行建议 100 字符内（中文 50 字内）

---

## 5. 质量检查清单

组装完成后逐项检查：

**必通过**：
- [ ] YAML name 与 domain_slug 一致
- [ ] description 包含 WHAT 和 WHEN 两部分
- [ ] 知识文档中每个工具在"工具调用"章节都有对应描述
- [ ] 知识文档中每条 Iron Rule 在"自检清单"中都有对应检查项
- [ ] 工具调用方式与目标环境适配器一致
- [ ] JSON 示例中的特殊字符已正确转义

**建议通过**：
- [ ] SKILL.md ≤ 500 行（如超过已正确拆分）
- [ ] 有至少 3 个完整示例
- [ ] 错误模式覆盖了最常见的 5 种以上
