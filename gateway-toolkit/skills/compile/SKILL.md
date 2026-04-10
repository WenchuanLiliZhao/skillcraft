---
name: compile-skill
description: |
  从知识文档（knowledge document）编译生成环境特定的 SKILL.md 文件。
  当用户要求"编译 skill""compile skill""从知识文档生成 skill""生成 SKILL.md"时触发。
  输入为一份知识文档 .md 文件，输出为可直接使用的 Cursor/Claude Code/AI Portal 环境的 SKILL.md。
  注意：仅在用户明确请求编译/生成 skill 文件时使用，不应被普通查询触发。
---

# Compile Command

从知识文档编译生成环境特定的 SKILL.md。

## 依赖文件（执行前加载）

| 文件 | 何时加载 | 必须 | 用途 |
|------|---------|------|------|
| [references/skeleton-template.md](references/skeleton-template.md) | Step 3 开始时 | ✅ | 构建流程章节的通用框架 + 填充指南 |
| [references/assembly-rules.md](references/assembly-rules.md) | Step 3 开始时 | ✅ | 各章节的组装逻辑 + 拆分规则 + 质量检查 |
| [adapters/cursor.md](adapters/cursor.md) | Step 2（目标=Cursor 时） | 三选一 | Cursor 环境工具调用模板 |
| [adapters/claude-code.md](adapters/claude-code.md) | Step 2（目标=Claude Code 时） | 三选一 | Claude Code 环境工具调用模板 |
| [adapters/portal.md](adapters/portal.md) | Step 2（目标=AI Portal 时） | 三选一 | AI Portal 环境工具调用模板 |

## 执行流程

```
Step 1: 读取知识文档 → 解析元数据和章节
Step 2: 检测目标环境 → Cursor / Claude Code / AI Portal
Step 3: 加载适配器 → 注入环境特定的工具调用方式
Step 4: 组装 SKILL.md → 按骨架模板填充各章节
Step 5: 自检 → 完整性、正确性、行数
Step 6: 输出 → 写入文件或展示给用户
```

---

### Step 1: 读取知识文档

1. 用户指定知识文档路径（或在当前对话中提供）
2. 解析 YAML 元数据头，提取：
   - `domain_slug` → 用作生成的 skill name
   - `one_liner` → 用于概述
   - `tools` → 用于工具定义章节和 description 生成
   - `api` → 用于适配器配置
3. 逐章节提取内容（按 `## ` 标题分割）：
   - Domain Overview, Tool Interface, Iron Rules, Semantic Framework
   - Request Specification, Output Specification, Examples, Error Patterns

如果缺少必填章节（Domain Overview / Tool Interface / Request Specification / Output Specification / Examples），停止并提示用户先用 Prepare 命令补充。

---

### Step 2: 环境检测

按以下优先级判断：

1. 用户明确指定 → 直接使用
2. 自动检测：
   - 当前环境有 `CallMcpTool` 可用 → **Cursor**
   - 当前环境有 `bash` 且存在 `claude` CLI → **Claude Code**
   - 其他 → 询问用户

读取对应适配器文件：
- Cursor → [adapters/cursor.md](adapters/cursor.md)
- Claude Code → [adapters/claude-code.md](adapters/claude-code.md)
- AI Portal → [adapters/portal.md](adapters/portal.md)

---

### Step 3: 组装 SKILL.md

按以下顺序组装（详见 [references/assembly-rules.md](references/assembly-rules.md)）：

#### 3.1 YAML 前置元数据

```yaml
---
name: {domain_slug}
description: |
  {自动生成，见下方 description 生成策略}
---
```

**description 生成策略**：

从知识文档自动组装，包含 WHAT 和 WHEN：

```
WHAT 部分:
  "{one_liner}。数据查询通过 {tool_1} / {tool_2} / ... 等工具完成。"

WHEN 部分:
  "触发场景包括但不限于：用户提到 {从典型用户表达中提取的关键词列表}。"

额外强调:
  从 Iron Rules 中提取最重要的 1-2 条作为 description 的补充。
```

#### 3.2 标题 + 概述

```markdown
# {domain} Skill

{one_liner}
```

#### 3.3 工具调用章节

从知识文档的 Tool Interface + 适配器模板生成：

对每个工具：
1. 从适配器读取该环境的**调用方式模板**
2. 用知识文档的工具参数**填充模板**
3. 从知识文档复制**调用示例**和**返回格式解析**

#### 3.4 硬性规则章节

从知识文档的 `## Iron Rules` **直接复制**。
- 保持原始编号、标题、✅/❌ 示例
- 在章节开头添加引导语："构建请求前，先逐条过一遍："

#### 3.5 语义理解章节

从知识文档的 `## Semantic Framework` **直接复制**。
- 包括 Decomposition Dimensions 和 Disambiguation Rules

#### 3.6 工具使用模式章节

从知识文档的 `## Tool Interface` 中提取每个工具的：
- 调用示例（用适配器模板格式化）
- 返回格式
- 返回解析规则

#### 3.7 请求格式规范章节

从知识文档的 `## Request Specification` **直接复制**。
- 包括 Parameters, Quick Reference Tables, Default Strategies, Filter Routing, Composition Constraints

#### 3.8 构建流程章节（自动生成）

这是**唯一需要自动组装**的章节。按骨架模板（见 [references/skeleton-template.md](references/skeleton-template.md)）生成：

```markdown
## 构建流程

步骤 0: 语义解析
  按语义理解框架分解用户请求。
  {如果有 Disambiguation Rules → 引用："逐条检查消歧规则"}

步骤 1: 数据检索
  {对每个工具 → 生成 "调用 {tool} 获取 {purpose}" 的指令}
  {如果有多工具 → 指明调用顺序和依赖关系}

步骤 2: 参数构造
  {从 Request Specification 的参数列表生成逐参数构造指令}
  {如果有 Filter Routing → 引用筛选条件决策树}
  {如果有 Composition Constraints → 引用组合约束}

步骤 3: 自检清单
  生成自检清单，每条 Iron Rule 对应一个检查项：
  {遍历 Iron Rules → 对每条生成 "✅ {规则标题概括为检查项}"}
  额外通用检查项：
  ✅ 工具返回的信息已正确解析
  ✅ 请求格式（转义、类型）正确
  ✅ 输出结构符合展示规范
```

#### 3.9 输出展示规范

从知识文档的 `## Output Specification` **直接复制**。

#### 3.10 完整示例

从知识文档的 `## Examples` **直接复制**。

#### 3.11 常见错误模式

从知识文档的 `## Error Patterns` **直接复制**。

---

### Step 4: 行数检查与拆分

组装完成后检查总行数：

**≤ 500 行** → 直接输出单文件 SKILL.md

**> 500 行** → 自动拆分为主文件 + references：

```
{domain_slug}/
├── SKILL.md              # 核心（<500 行）
└── references/
    ├── examples.md       # 完整示例
    ├── error-patterns.md # 错误模式
    └── param-spec.md     # 详细参数规范
```

**拆分优先级**（先移走优先级低的，直到 SKILL.md < 500 行）：
1. 完整示例（通常最长，~250 行）→ `references/examples.md`
2. 错误模式 → `references/error-patterns.md`
3. 详细参数规范 → `references/param-spec.md`

**留在 SKILL.md 中不可拆分的**：
- YAML 元数据 + 概述
- 工具调用
- 硬性规则（必须常驻上下文）
- 语义理解框架
- 构建流程 + 自检清单
- 输出展示规范

**拆分后在 SKILL.md 中添加引用**：
```markdown
## 参考文件
- 完整示例见 [examples.md](references/examples.md)
- 错误模式见 [error-patterns.md](references/error-patterns.md)
- 详细参数规范见 [param-spec.md](references/param-spec.md)
```

---

### Step 5: 自检

组装完成后执行以下检查，向用户报告结果：

**结构完整性**：
- [ ] YAML 元数据的 name 和 description 非空
- [ ] description 包含 WHAT（做什么）和 WHEN（何时触发）
- [ ] 所有必要章节都存在（工具调用、构建流程、输出规范）
- [ ] 如有 Iron Rules，自检清单中每条都有对应项

**格式正确性**：
- [ ] JSON 示例中的字符串内双引号已转义为 `\"`
- [ ] 工具调用方式与目标环境一致
- [ ] 粒度后缀等技术标识格式正确（如全小写）

**可用性**：
- [ ] 一个不了解此领域的 AI，能否仅凭此 SKILL.md 正确执行任务？
- [ ] 如有拆分，references 中的文件链接正确？

---

### Step 6: 输出

根据环境输出到对应位置：

| 环境 | 输出路径 | 方式 |
|------|---------|------|
| Cursor | `skills/{domain_slug}/SKILL.md` | 直接写入文件 |
| Claude Code | 项目根目录或 `AGENTS.md` | 写入文件或追加 |
| AI Portal | 控制台 | 展示完整内容供复制 |

输出后向用户报告：
```
✅ Skill 已生成：
   路径: skills/{domain_slug}/SKILL.md
   行数: {N} 行{如拆分: + references/ 下 {M} 个文件}
   环境: {environment}

   自检结果: {通过数}/{总数} 项通过
   {如有未通过项 → 列出}

   下一步: 试试向 AI 说 "{典型用户表达}" 看 skill 是否正确触发。
```

---

