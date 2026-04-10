# Skill Compiler

将人工维护的 AI Skill 替换为两步自动化流程：**Prepare**（提取知识）和 **Compile**（编译 Skill）。

知识文档作为中间产物持久化保存，按需编译为 Cursor / Claude Code / AI Portal 三种环境的 SKILL.md。

---

## 快速开始

### 1. 配置凭证

```bash
cp .env.local.example .env.local
# 编辑 .env.local，填入你的 Gateway URL 和 API Key
```

### 2. 为新 API 创建 Skill

```
向 AI 说："使用 prepare-skill，为 {API 名称} 创建知识文档"
↓ AI 自动探索 API → 访谈业务规则 → 生成知识文档 (.md)
↓ 审阅知识文档，补充/修正

向 AI 说："使用 compile-skill，把 {知识文档路径} 编译为 Cursor skill"
↓ AI 读取知识文档 → 检测环境 → 组装 SKILL.md → 写入文件
```

### 3. 编译到不同环境

```
"把 knowledge-doc-metric-query.md 编译为 Claude Code skill"
"把 knowledge-doc-metric-query.md 编译为 AI Portal skill"
```

---

## 目录结构

```
.
├── skills/                     # AI Skills（核心）
│   ├── prepare/                #   知识提取
│   ├── compile/                #   Skill 编译
│   └── skill-creator/          #   评估工具（第三方）
│
├── research/                   # 研究过程（参考）
│   ├── plans/                  #   构建计划 & 产出物
│   └── reports/                #   早期测试报告
│
├── .env.local.example          # 凭证模板
├── .gitignore
└── .cursor/skills -> skills    # Cursor 兼容 symlink
```

> `.cursor/skills` 是指向 `skills/` 的符号链接，确保 Cursor IDE 自动发现 skills。

---

## 核心概念

### 知识文档（Knowledge Document）

Prepare 和 Compile 之间的中间产物。以 Markdown 存储某个领域的全部业务规则和 API 用法，与运行环境无关。

格式规范见 `research/plans/outputs/02-knowledge-doc-spec.md`。

### 环境适配器（Environment Adapter）

| 环境 | 适配器 | 工具调用方式 | 输出位置 |
|------|--------|------------|---------|
| Cursor | `skills/compile/adapters/cursor.md` | `CallMcpTool` 或直接调用 | `skills/{name}/SKILL.md` |
| Claude Code | `skills/compile/adapters/claude-code.md` | `mcp__server__tool` 或 bash curl | `AGENTS.md` |
| AI Portal | `skills/compile/adapters/portal.md` | 平台内置函数 | 控制台输出 |

---

## 凭证管理

将 `.env.local.example` 复制为 `.env.local` 并填入真实值。`.env.local` 已在 `.gitignore` 中，不会被提交。

```
CAN_GATEWAY_URL=https://your-gateway-url.example.com
CAN_API_KEY=your-api-key-here
```

---

## 已知限制

来自端到端验证（`research/plans/outputs/05-validation-report.md`）：

| 问题 | 状态 |
|------|------|
| 知识文档示例数量不足（8/17） | 待修复：Examples 最低要求提至 15+ |
| 输出规范缺具体演示 | 待修复：需含完整输出示例 |
| Prepare 对高级 API 语法收集不足 | 已知限制：依赖被访者使用深度 |
| Cursor 适配器缺回退模板 | 待修复 |
