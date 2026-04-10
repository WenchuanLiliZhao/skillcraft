# Cursor 环境适配器

## 环境标识

- **检测方式**：当前会话中 `CallMcpTool` 工具可用
- **特征**：通过 MCP 协议调用外部工具，文件读写通过 IDE 工具完成

## 工具调用方式

### MCP 工具（知识文档中标记 `mcp_server` 的工具）

```
调用方式: CallMcpTool
参数:
  server: "{mcp_server_name}"     # 知识文档 Tool Interface 的 mcp_server 字段
  toolName: "{tool_name}"          # 知识文档 Tool Interface 的 tool_name 字段
  arguments: { ...参数对象... }     # 知识文档 Tool Interface 的参数定义
```

**模板**：
```markdown
调用 **{tool_display_name}** 工具：
- 工具：`CallMcpTool(server="{mcp_server_name}", toolName="{tool_name}")`
- 参数：
  {对每个参数:}
  - `{param_name}` ({type}, {required/optional}): {description}
```

**调用示例模板**：
```markdown
> 示例调用：
> ```
> CallMcpTool:
>   server: "{mcp_server_name}"
>   toolName: "{tool_name}"
>   arguments:
>     {param_1}: {value_1}
>     {param_2}: {value_2}
> ```
```

### HTTP 工具（知识文档中标记 `http_endpoint` 的工具）

```
调用方式: Shell 工具执行 curl 命令
认证: 从配置文件读取 API Key，添加到请求头
```

**模板**：
```markdown
通过 Shell 工具执行 HTTP 请求：
- 端点：`{http_method} {base_url}{endpoint}`
- 认证：从 `{config_file_path}` 读取 API Key
- 参数：
  {对每个参数:}
  - `{param_name}` ({type}, {required/optional}): {description}
```

**调用示例模板**：
```markdown
> 示例调用：
> ```bash
> # 先从配置文件读取 API Key
> API_KEY=$(grep 'api_key' {config_file_path} | ...)
>
> curl -X {method} "{base_url}{endpoint}" \
>   -H "Authorization: Bearer $API_KEY" \
>   -H "Content-Type: application/json" \
>   -d '{...请求体...}'
> ```
```

## 输出路径

```
skills/{domain_slug}/
├── SKILL.md
└── references/          # 如有拆分
    ├── examples.md
    ├── error-patterns.md
    └── param-spec.md
```

## 特殊注意

- Cursor 的 SKILL.md 通过 `description` 字段进行触发匹配，关键词覆盖面要广
- Cursor 中 MCP 工具的认证由 Server 内部处理，SKILL.md 中不需要传递 token
- 文件路径使用相对路径（相对于 `skills/{domain_slug}/`）
- `.cursor/skills/` 是 `skills/` 的 symlink，Cursor 自动发现仍正常工作
