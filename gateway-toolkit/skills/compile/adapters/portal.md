# AI Portal 环境适配器

## 环境标识

- **检测方式**：用户明确指定目标为 AI Portal，或知识文档元数据中 `target_env` 包含 `portal`
- **特征**：工具作为平台内置函数直接调用，认证由平台自动处理

## 工具调用方式

### 平台内置函数（知识文档中标记 `mcp_server` 或 `portal_function` 的工具）

```
调用方式: 直接调用内置函数
认证: 平台自动处理，无需手动传递
参数: 直接传递
```

**模板**：
```markdown
调用内置函数 **{function_name}**：
- 参数：
  {对每个参数:}
  - `{param_name}` ({type}, {required/optional}): {description}
```

**调用示例模板**：
```markdown
> 调用示例：
> ```
> {function_name}({
>   {param_1}: {value_1},
>   {param_2}: {value_2}
> })
> ```
```

### HTTP 工具（知识文档中标记 `http_endpoint` 的工具）

Portal 环境通常将 HTTP API 封装为内置函数，但如果需要直接调用：

```
调用方式: 平台提供的 HTTP 请求函数
认证: 通过平台的 credential store 自动注入
```

**模板**：
```markdown
通过平台 HTTP 函数调用：
```
http_request({
  method: "{method}",
  url: "{base_url}{endpoint}",
  headers: { "Content-Type": "application/json" },
  body: { ...请求体... }
})
```
认证信息由平台自动注入，无需手动配置。
```

## 输出路径

AI Portal 的 skill 不写入文件系统，而是输出到控制台：

```
将完整的 SKILL.md 内容输出到控制台。
用户复制后粘贴到 Portal 的 skill 配置界面。

输出格式：
  1. 先输出元数据摘要（名称、描述、触发关键词）
  2. 再输出用 ``` 包裹的完整 SKILL.md 内容
  3. 如有 references/ 文件，逐个输出
```

## 特殊注意

- Portal 环境下不需要文件路径操作，所有内容通过控制台交付
- 认证完全由平台处理，SKILL.md 中不应包含任何认证相关说明
- 如果 Portal 有特定的 skill 格式要求（如 JSON schema），Compile 命令应询问用户并适配
- 函数名映射：知识文档中的 `tool_name` 可能需要映射为 Portal 的内部函数名，这个映射关系应在编译时由用户确认
