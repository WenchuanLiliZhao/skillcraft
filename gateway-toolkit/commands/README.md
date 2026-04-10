# Plans Outputs — 产出物目录

这些文件是 Plan 1-5 的**产出物（参考文档）**，不是可执行的 skills。

可执行的 skills 在仓库根目录 `skills/` 下：
- `prepare/` — 从 API + 用户访谈中提取知识，生成知识文档
- `compile/` — 从知识文档编译生成环境特定的 SKILL.md

---

## 文件清单（按依赖顺序）

| 序号 | 文件 | 来源 | 用途 |
|------|------|------|------|
| 01 | `01-skeleton.md` | Plan 1 | 通用 Skill 骨架 — 定义 SKILL.md 的 10 个标准章节及其分类（U/D/E/T） |
| 02 | `02-knowledge-doc-spec.md` | Plan 2 | 知识文档格式规范 — 定义 Prepare 命令输出 / Compile 命令输入的标准格式 |
| 03 | `03-knowledge-doc-example-metric-query.md` | Plan 2 | 知识文档示例 — 指标查询领域（由当时手写 SKILL 整理） |
| 04 | `04-generated-skill.md` | Plan 5 | 编译产出 — 模拟 Compile 命令从 03 生成的 SKILL.md（Cursor 环境） |
| 05 | `05-validation-report.md` | Plan 5 | 验证报告 — 04 与基准手写 SKILL 的逐章节对比、覆盖度评分、改进清单 |

## 依赖关系

```
01-skeleton ──→ compile-skill（骨架模板）
02-knowledge-doc-spec ──→ prepare-skill（输出格式）+ compile-skill（输入格式）
03-knowledge-doc-example ──→ 04-generated-skill（编译输入）
04-generated-skill ──→ 05-validation-report（端到端验证结论；基准为当时手写 SKILL，见报告内文）
```
