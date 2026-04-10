# Claude Code 环境适配器

## 环境标识

- **检测方式**：当前环境为终端 + `claude` CLI 可用
- **特征**：所有工具通过 bash 命令调用，支持 MCP 协议（通过 `mcp__` 前缀）

## 工具调用方式

### MCP 工具（知识文档中标记 `mcp_server` 的工具）

Claude Code 支持 MCP，但调用格式不同于 Cursor：

```
调用方式: mcp__{server_name}__{tool_name}
参数: 直接传递 JSON 对象
```

**模板**：
```markdown
调用 **{tool_display_name}** 工具：
- 工具名：`mcp__{mcp_server_name}__{tool_name}`
- 参数：
  {对每个参数:}
  - `{param_name}` ({type}, {required/optional}): {description}
```

**调用示例模板**：
```markdown
> 使用 MCP 工具：
> 工具: `mcp__{mcp_server_name}__{tool_name}`
> 参数:
> ```json
> {
>   "{param_1}": {value_1},
>   "{param_2}": {value_2}
> }
> ```
```

### HTTP 工具（知识文档中标记 `http_endpoint` 的工具）

```
调用方式: bash 中执行 curl 命令
认证: 从环境变量读取 ($API_KEY, $BASE_URL 等)
```

**模板**：
```markdown
执行以下命令查询数据：
```bash
curl -X {method} "$BASE_URL{endpoint}" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...请求体...}'
```
```

**认证配置**：
```markdown
> 使用前确保设置环境变量：
> ```bash
> export BASE_URL="{base_url}"
> export API_KEY="{api_key_来源说明}"
> ```
```

## 输出路径

Claude Code 支持两种 skill 放置方式：

**方式 1：独立目录**（推荐）
```
.claude/skills/{domain_slug}/
├── SKILL.md
└── references/
```

**方式 2：AGENTS.md 追加**
```
将生成内容追加到项目根目录的 AGENTS.md 文件末尾。
适用于简短 skill（< 200 行）。
```

## 特殊注意

- Claude Code 的 SKILL.md 触发机制依赖 AGENTS.md 或 `.claude/` 目录约定
- 环境变量是首选的认证方式，不要在 SKILL.md 中硬编码任何密钥
- MCP 工具名使用双下划线 `__` 分隔 server 和 tool，注意命名规范
- bash 代码块中使用 `set -e` 确保错误立即停止
