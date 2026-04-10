---
domain: "指标数据查询"
domain_slug: "metric-query"
one_liner: "根据用户自然语言描述，通过语义层 API 查询指标数据"
target_users: "业务分析师、运营人员（非技术用户）"
language: "zh-CN"

api:
  base_url: "从 .env.local 读取 CAN_GATEWAY_URL（见 .env.local.example）"
  auth_method: "API Key（由工具内部处理，无需手动传递）"
  request_format: "JSON"

tools:
  - name: "search_metrics"
    display_name: "搜索指标"
    purpose: "根据关键词搜索可用指标，返回指标名称、展示名、业务口径"
    params:
      - name: "keyword"
        type: "string"
        required: true
        description: "搜索关键词，支持逗号分隔批量搜索"
      - name: "pageSize"
        type: "number"
        required: false
        description: "返回数量，默认 5"
    returns: "纯文本，每行一个指标：metricName | displayName | description (dims count)"

  - name: "get_dimensions"
    display_name: "查询维度"
    purpose: "查询指标的可分析维度及维度值样本，支持批量查询自动计算维度交集"
    params:
      - name: "metricNames"
        type: "string"
        required: true
        description: "指标名称，多个用逗号分隔"
      - name: "keyword"
        type: "string"
        required: false
        description: "过滤关键词，只返回匹配的维度"
    returns: "纯文本，每行一个维度：dimName(displayName): sampleValue1, sampleValue2, ..."

  - name: "query_metrics"
    display_name: "执行查询"
    purpose: "向语义层 API 发送查询请求，返回数据结果"
    params:
      - name: "requestBody"
        type: "json"
        required: true
        description: "完整的 JSON 请求体字符串"
    returns: "查询结果数据"

created_by: "manual (从 SKILL.md 提取)"
created_at: "2026-04-10"
version: 1
---

## Domain Overview

本领域是**指标平台（语义层）数据查询**。用户用自然语言描述数据需求，AI 通过工具检索可用指标和维度，构造 JSON 请求体发送给语义层 API，再将结果以业务语言呈现。

典型用户表达：
- "上月各渠道的销售额是多少？"
- "本年至今的日均客单价及同比增长率"
- "Wholesale 渠道的销售额在所有渠道中占比多少？"
- "上月环比增速前 5 的品牌"
- "近 30 天各门店的退货率排名"

工作流：用户提问 → AI 搜索指标 → AI 查询维度 → AI 构建 JSON 请求体 → AI 调用查询 API → AI 以「查询解读 + JSON + 结果」三段式展示。

**核心约束**：构建查询前，必须先通过工具检索指标和维度信息，禁止凭记忆猜测指标名或维度名。

## Tool Interface

### 搜索指标 (`search_metrics`)

**用途**: 根据业务关键词搜索可用的指标

**参数**:
- `keyword` (string, 必填): 搜索关键词，支持逗号分隔批量搜索（中英文逗号均可）
- `pageSize` (number, 选填): 每个关键词的返回数量，默认 5

**调用示例**:
- 单个关键词: `keyword: "客单价", pageSize: 5`
- 批量搜索: `keyword: "客单价,销售额", pageSize: 3`

**返回格式**:
```
[客单价] 3 metric(s):
- AOV | 客单价 | 销售金额/购买客户数 (53 dims)
- l7d_AOV | 近7天客单价 [DERIVED] (53 dims)

[销售额] 2 metric(s):
- retail_amt | 销售金额 | 销售金额求和 (53 dims)
```

**返回解析规则**:
- 行首英文名（如 `AOV`）是 metricName → 放入 `metrics` 数组
- `|` 后第一段（如 `客单价`）是 displayName → 用于查询解读的中文展示
- `|` 后第二段（如 `销售金额/购买客户数`）是 description → 用于查询解读的业务口径
- `[DERIVED]` 标记 = 派生指标，使用前必须验证其语义与用户意图完全一致
- `(53 dims)` = 该指标的可用维度数量

---

### 查询维度 (`get_dimensions`)

**用途**: 查询指标的可分析维度，包含维度值样本；批量查询时自动计算维度交集

**参数**:
- `metricNames` (string, 必填): 指标名称，多个用逗号分隔
- `keyword` (string, 选填): 过滤关键词，只返回名称或值匹配的维度

**调用示例**:
- 单指标: `metricNames: "AOV"`
- 单指标 + 过滤: `metricNames: "AOV", keyword: "渠道"`
- 批量（自动算交集）: `metricNames: "AOV,retail_amt", keyword: "渠道"`

**返回格式（单指标）**:
```
Metric '客单价' (AOV), 53 dimension(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale
- gender(性别): 女, 男
```

**返回格式（批量）**:
```
## 客单价 (AOV), 2 dim(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale

## 销售金额 (retail_amt), 2 dim(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale

## COMMON dimensions (intersection), 2 dim(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale
```

**返回解析规则**:
- 行首英文名（如 `first_channel`）是 dimName → 放入 `dimensions` / `filters`
- 括号内（如 `一级渠道`）是 displayName → 用于查询解读
- 冒号后是维度值样本 → 用于 filters/resultFilters 的值匹配（必须严格按原始写法，含大小写和空格）
- `COMMON dimensions` 是多指标共有维度的交集 → 多指标查询时 dimensions 只能从这里选
- `metric_time` 是所有指标的默认可分析维度，支持粒度后缀：`__day`, `__month`, `__year`, `__week`, `__quarter`

---

### 执行查询 (`query_metrics`)

**用途**: 发送完整的 JSON 请求体，执行数据查询

**参数**:
- `requestBody` (json, 必填): 完整的 JSON 请求体字符串

**调用示例**:
- `requestBody: '{"metrics": ["AOV"], "timeConstraint": "[\'metric_time__day\']= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"DAY\")"}'`

**返回格式**: 查询结果数据（表格形式）

## Iron Rules

### 规则 0 — 每次查询必须输出「查询解读」，且在 JSON 之前

向用户展示时，必须先输出查询解读（自然语言解释），然后是请求 JSON，最后是查询结果。三段缺一不可，顺序不可颠倒。

✅ 正确: 📊 查询解读 → 📋 请求 JSON → 📈 查询结果
❌ 错误: 直接展示 JSON 或结果，跳过查询解读

### 规则 1 — 相对时间必须用 NOW()，禁止硬编码日期

"上月""昨天""近N天"等相对时间表达 → 必须用 `NOW()` 函数。包括 `timeConstraint` 和 `period` 锚定。

✅ 正确: `DATEADD(DateTrunc(NOW(), "MONTH"), -1, "MONTH")`
❌ 错误: `DATEADD(DateTrunc('2026-03-05', "MONTH"), -1, "MONTH")`

⚠️ 易错场景: `period` 锚定的 `timeConstraint` 也必须用 NOW()。当使用 `metricDefinitions + period` 时，锚定日期用 `DATEADD(DateTrunc(NOW(), "DAY"), -1, "DAY")` 表示昨天，不可将当前日期硬编码。

唯一例外：用户明确说了 "2025年4月" 这样的具体日期 → 才可用字面日期。

### 规则 2 — metricDefinitions 中每个 key 必须同时在 metrics 数组中

定义了临时指标就必须注册到 `metrics`。包括仅作为 `expr` 中间计算变量的辅助指标。

✅ 正确: `"metrics": ["total", "ratio"]` + `"metricDefinitions": { "total": {...}, "ratio": { "expr": "[val]/[total]" } }`
❌ 错误: `"metrics": ["ratio"]` + `"metricDefinitions": { "total": {...}, "ratio": { "expr": "[val]/[total]" } }`（total 未注册）

### 规则 3 — 占比/排名 + filters = 分母/范围被缩小，结果恒 100%/恒为 1

要"某个值在全局中的占比/排名" → 用 `resultFilters` 做展示筛选，不用 `filters`。

✅ 正确: `"resultFilters": ["[first_channel]= \"Wholesale\""]` → 分母包含所有渠道
❌ 错误: `"filters": ["[first_channel]= \"Wholesale\""]` → 只剩 Wholesale 自己，占比恒 100%

⚠️ 易错场景: "Wholesale 渠道的占比"含义是 Wholesale 在所有渠道中的占比。`dimensions` 必须包含渠道维度，用 `resultFilters` 仅展示 Wholesale 行。

### 规则 4 — "同比"默认 = yoy；带粒度前缀时按前缀选择

| 用户说 | 映射 |
|--------|------|
| "同比"（无限定） | yoy |
| "年同比" | yoy |
| "月同比" | mom |
| "周同比" | wow |
| "季同比" | qoq |

⚠️ 中文"同比"单独出现时，一律映射为 yoy，不可映射为 mom/qoq/wow。

### 规则 5 — 一个指标只能做一次快速计算，不可链式叠加

需要多步（如先算环比再排名）→ 用 `metricDefinitions` 分步。

✅ 正确: 先定义 `mom_growth` 临时指标，再对它做 `mom_growth__rankDense__desc__first_channel`
❌ 错误: `retail_amt__sameperiod__mom__growth__rank__desc__first_channel`（链式叠加）

### 规则 6 — MetricMatches 只能在 metricDefinitions 的 filters 中使用

✅ 正确: `"metricDefinitions": { "temp": { "filters": ["MetricMatches(...)"] } }`
❌ 错误: `"filters": ["MetricMatches(...)"]`（顶层 filters 不支持）

### 规则 7 — 派生指标的 metric_time 粒度限制必须遵守

标注"仅支持日粒度"的派生指标（如 `sales_yoy`），只能在 `timeConstraint` 锚定到天粒度时使用。

✅ 正确: 上月销售额同比 → `retail_amt__sameperiod__yoy__growth`（原子指标+快速计算）
❌ 错误: 上月销售额同比 → `sales_yoy`（日粒度派生指标 + 月级 timeConstraint = 不兼容）

### 规则 8 — "月变化趋势"中的占比/排名范围维度必须是 metric_time__month

✅ 正确: `retail_amt__proportion__metric_time__month`（每月内各渠道占比）
❌ 错误: `retail_amt__proportion__`（全局占比，无月内分组 → 跨月混淆）
❌ 错误: `retail_amt__proportion__first_channel`（每渠道内占比 → 恒100%）

### 规则 9 — 上下文不足时必须拒绝生成查询

生成 JSON 前，必须通过以下三项检查，任一不通过则拒绝并返回空 `{}`：
- **检查 A**: 候选指标能否覆盖用户需求？（无 → 禁止虚构指标名）
- **检查 B**: 所选维度是否在指标的可分析维度内？（不在 → 禁止使用）
- **检查 C**: 用户消息是否包含查询意图？（纯问候 → 返回空 JSON）

## Semantic Framework

### Decomposition Dimensions

将用户请求分解为以下四个维度：

| 维度 | 核心问题 | 对应 API 参数 | 示例 |
|------|----------|-------------|------|
| 看什么（指标） | 用户要看的业务量是什么？ | `metrics` | "销售额""客单价""日均订单数" |
| 怎么看（分析方式） | 直接看值？对比？占比？排名？ | 快速计算后缀 / `metricDefinitions` | "同比增长率""占比""排名前5" |
| 看谁的（维度&筛选） | 按什么拆分？筛选哪些？ | `dimensions` / `filters` / `resultFilters` | "各品牌""某渠道""某地区" |
| 看哪段时间 | 时间范围？时间对比？ | `timeConstraint` | "上月""近7天""某月vs另一月" |

### Disambiguation Rules

#### 规则 A — "总和" vs "分别"

| 用户说 | 含义 | dimensions 处理 |
|--------|------|----------------|
| "A 和 B 的指标分别是多少" | 按 A、B 分组展示 | 保留维度 |
| "A 和 B 的指标总和" | 合并为一个数字 | 不放该维度 |
| "A 和 B 的指标"（无修饰） | 歧义，默认"分别" | 保留维度 |

#### 规则 B — 修饰语的作用域

"日均/月均/平均"修饰紧跟其后的所有并列项：
- "各时段的日均某指标" → 所有时段都算日均
- "总指标A和日均指标B" → A 取总量，B 取日均

#### 规则 C — "占比"的两种含义

| 用户说 | 含义 | 实现方式 |
|--------|------|---------|
| "销售额占比" | 值占比 | 直接用 `proportion` 快速计算 |
| "款色占比""客户占比" | 数量占比 | 先用计数指标统计数量，再对计数指标做 `proportion` |

判断标准：占比前面是实体类型（款色、客户、门店）→ 数量占比；是指标名（销售额、订单数）→ 值占比。

#### 规则 D — "XX均"的聚合维度

"XX均"中的"XX"就是聚合维度：
- "店均" → `multi_level_agg__avg,{门店维度}`
- "人均" → `multi_level_agg__avg,{客户维度}`

#### 规则 E — "同比" vs "环比"

| 用户说 | 映射 | 说明 |
|--------|------|------|
| "同比"（无限定） | yoy | 默认=年同比 |
| "环比" | 根据时间粒度选 | 日→dod，周→wow，月→mom，季→qoq |

#### 规则 F — "对比去年末" ≠ "年同比"

| 用户说 | 含义 | 实现方式 |
|--------|------|---------|
| "同比" | 与去年同期对比 | `__sameperiod__yoy__growth` |
| "与去年末相比" | 与去年12月/去年最后一天对比 | `metricDefinitions + period` 定位去年末 |

#### 规则 G — "趋势" ≠ 同环比

"趋势"/"变化趋势" = 按时间展开看值的变化。除非用户明确提到"同比""环比"，否则不要额外添加同环比。

#### 规则 H — "差异/差距/对比" ≠ 同环比

"各XX之间的差异" = 直接查出各自的值让用户比较，不是同比/环比。

#### 规则 I — 简单优先

如果用户问题可以用简单查询回答，就不要添加不必要的 `metricDefinitions`、同环比、占比、排名。例如：
- "各渠道的销售额" → 直接查，不需要额外计算
- "上月总销售额" → 只需 `retail_amt` + `timeConstraint`，`dimensions` 为空

#### 规则 J — 无年份日期默认当年

用户提到日期但未指定年份时，默认指当前年份。参考 system prompt 中的 Current date。

## Request Specification

### Parameters

#### metrics (必填) — 指标列表

```json
"metrics": ["metric_A", "metric_B"]
```

支持快速计算后缀（每个指标只能应用一次，不可链式叠加）：

**同环比**: `{指标}__sameperiod__{偏移粒度}__{方法}`

偏移粒度:

| 用户说 | 粒度 | 用户说 | 粒度 |
|--------|------|--------|------|
| 日环比 | dod | 对比上月末 | moeom |
| 周环比 | wow | 对比上季末 | qoeoq |
| 月环比 | mom | 对比去年末 | yoeoy |
| 季环比 | qoq | 对比上月初 | mosom |
| 年同比 | yoy | 对比去年初 | yosoy |

所有偏移粒度支持 `{N}_` 前缀（如 `-2_yoy` = 2年前同期）。

方法:

| 用户说 | 方法 | 计算 |
|--------|------|------|
| 同期/环比的值 | value | 对比期原值 |
| 增长了多少 | growth | 当前 − 对比 |
| 增长率/增速 | growth | (当前 − 对比) / 对比 |
| 下降了多少 | decrease | 对比 − 当前 |
| 下降率 | decreaserate | (对比 − 当前) / 对比 |

约束: `metric_time` 须在 `dimensions` 或 `timeConstraint` 中出现；偏移粒度不可小于 `metric_time` 粒度。

**占比**: `{指标}__proportion__{范围维度}`

| 范围维度写法 | 分母 |
|-------------|------|
| `proportion__`（末尾两个下划线） | 全部数据汇总（全局占比） |
| `proportion__dim_A` | 按 dim_A 每组分别汇总（组内占比） |

前提: `dimensions` 必须包含参与占比计算的实体维度。

**排名**: `{指标}__{方式}__{顺序}__{范围维度}`

方式: `rank`（并列跳号）/ `rankDense`（并列不跳）/ `rowNumber`（不并列）
顺序: `desc`（大=1）/ `asc`（小=1）
范围维度: 省略=全局；填维度=组内排名

**时间限定**: `{指标}__period__{限定}`

| 类型 | 语法示例 |
|------|---------|
| 近N期 | 7d, 3w, 6m, 2q, 1y |
| 本期至今 | ytd, qtd, mtd, wtd |
| 当前期间 | cy, cq, cm, cw, cd |

---

#### metricDefinitions (选填) — 临时指标定义

每个 key 必须同时出现在 `metrics` 数组中（铁律 2）。临时指标名必须与已有指标不同。

可配置属性:

| 属性 | 说明 | 约束 |
|------|------|------|
| refMetric | 引用已有指标 | |
| expr | 复合表达式 `"[m1]+[m2]"` | 可引用其他临时指标 |
| period | 时间限定 | 仅支持相对偏移；of 后粒度不可细于 timeConstraint 粒度 |
| metricGrain | 时间粒度 | DAY/WEEK/MONTH/QUARTER/YEAR |
| preAggs | 时间维度多层聚合 | 格式为数组 `[{...}]`；必须配合 period |
| filters | 业务限定 | 支持维度筛选和 MetricMatches |
| indirections | 衍生方式 | 同环比/占比/排名/多层聚合 |
| specifyDimension | 聚合维度控制 | EXCLUDE 排除外层分组影响 |

**period 语法**:

| 类型 | 语法 | 含义 |
|------|------|------|
| to_date | `to_date -6 day of 0 day` | 基准日前6天~基准日（共7日） |
| grain_to_date | `grain_to_date 0 year of 0 day` | 本年初~基准日 |
| relative_date | `relative_date -1 month of 0 day` | 上月 |
| SPECIFY_DATE | `SPECIFY_DATE end day of -1 year` | 上年最后一天 |

**preAggs**: `[{"granularity": "DAY", "calculateType": "AVG"}]`
- granularity: DAY / WEEK / MONTH / QUARTER / YEAR
- calculateType: AVG / MAX / MIN

**indirections 示例**:
- `["sameperiod__yoy__value"]` → 年同比值
- `["proportion__dim_A"]` → dim_A 组内占比
- `["multi_level_agg__avg,dim_A"]` → 非时间维度多层聚合

---

#### dimensions (选填) — 分析维度

```json
"dimensions": ["metric_time__month", "dim_A"]
```

日期维度支持粒度后缀（必须全部小写）: `__year`, `__quarter`, `__month`, `__week`, `__day`

多指标查询时，dimensions 只能包含所有指标都支持的维度（取交集）。

---

#### filters 与 resultFilters

| | filters | resultFilters |
|---|---------|--------------|
| 等价 SQL | WHERE | HAVING |
| 影响计算 | 是 | 否（仅过滤返回行） |

filters 语法: `[dim]= "value"` / `IN([dim], "v1", "v2")` / `NotIn(...)` / `contains(...)` / 数值比较 / 日期比较

resultFilters 语法: `[metric] > 1000` / `[dim]= "value"`

---

#### timeConstraint (选填) — 时间范围

两个角色: A-时间范围过滤（一个区间）；B-period 锚定基准（一个具体日期/月份）。

### Quick Reference Tables

**timeConstraint 速查表**:

| 用户说 | timeConstraint |
|--------|---------------|
| 昨天 | `"['metric_time__day']= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"DAY\")"` |
| 今天 | `"['metric_time__day']= DateTrunc(NOW(), \"DAY\")"` |
| 上周 | `"DateTrunc(['metric_time'], \"WEEK\") = DATEADD(DateTrunc(NOW(), \"WEEK\"), -1, \"WEEK\")"` |
| 上月 | `"DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")"` |
| 本月 | `"DateTrunc(['metric_time'], \"MONTH\") = DateTrunc(NOW(), \"MONTH\")"` |
| 上季 | `"DateTrunc(['metric_time'], \"QUARTER\") = DATEADD(DateTrunc(NOW(), \"QUARTER\"), -1, \"QUARTER\")"` |
| 本年 | `"DateTrunc(['metric_time'], \"YEAR\") = DateTrunc(NOW(), \"YEAR\")"` |
| 去年 | `"DateTrunc(['metric_time'], \"YEAR\") = DATEADD(DateTrunc(NOW(), \"YEAR\"), -1, \"YEAR\")"` |
| 近7天 | `"DateTrunc(['metric_time'], \"DAY\") >= DATEADD(DateTrunc(NOW(), \"DAY\"), -7, \"DAY\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")"` |
| 近30天 | `"DateTrunc(['metric_time'], \"DAY\") >= DATEADD(DateTrunc(NOW(), \"DAY\"), -30, \"DAY\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")"` |
| 近12个月 | `"DateTrunc(['metric_time'], \"MONTH\") >= DATEADD(DateTrunc(NOW(), \"MONTH\"), -12, \"MONTH\") AND DateTrunc(['metric_time'], \"MONTH\") < DateTrunc(NOW(), \"MONTH\")"` |
| 具体月份 2025年4月 | `"DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\""` |
| 具体日期 2025-06-15 | `"['metric_time__day']= \"2025-06-15\""` |

### Default Strategies

当用户未指定时间时（命中第一行即停）:

| 优先级 | 条件 | 默认 timeConstraint | 原因 |
|--------|------|--------------------|------|
| 1 | 有 period / __period__ / 时间限定派生指标 | 锚定昨天 | period 自身定义窗口 |
| 2 | 有 __sameperiod__mom__ | 上月 | 月环比需要月级时间 |
| 3 | 有 __sameperiod__wow__ | 上周 | |
| 4 | 有 __sameperiod__qoq__ | 上季 | |
| 5 | 有 __sameperiod__yoy__ | 上月 | |
| 6 | 有 __sameperiod__dod__ | 昨天 | |
| 7 | 有排名/TOP-N 且无时间维度 | 近30天或上月 | 排名需足够数据量 |
| 8 | dimensions 含 metric_time__month | 近12个月 | |
| 9 | dimensions 含 metric_time__quarter | 本年 | |
| 10 | dimensions 含 metric_time__week | 近12周 | |
| 11 | 其他 | 近7天 | 兜底 |

### Filter Routing

| 场景 | 放在 | 原因 |
|------|------|------|
| 筛选字段是时间相关 | `timeConstraint` | 禁止放 filters |
| 筛选字段是指标值/计算结果 | `resultFilters` | |
| 维度值筛选，需影响计算 | `filters` | |
| 维度值筛选，但不应影响占比/排名 | `resultFilters` | 避免缩小分母/范围 |
| 普通维度值筛选 | `filters` | |

### Composition Constraints

| 操作A | 操作B | 是否可组合 | 正确做法 |
|-------|-------|-----------|---------|
| 同环比 | 排名 | ❌ 不可链式 | metricDefinitions 分步：先定义同环比临时指标，再对它排名 |
| 同环比 | 占比 | ❌ 不可链式 | 同上 |
| period+preAggs | 同环比 | ❌ 不可叠加 | 分别定义今年和去年的临时指标（各含 period+preAggs），再用 expr 算增长率 |
| period（无 preAggs） | 同环比 | ✅ 用 indirections | `"indirections": ["sameperiod__yoy__growth"]` |
| multi_level_agg | 外层同维度 | ❌ 恒等于自身 | 添加 `specifyDimension: { "type": "EXCLUDE", "dimensions": "dim_X" }` |

### Other Parameters

- `orders`: 排序列须在 `metrics` 或 `dimensions` 中。格式 `[{"field": "asc/desc"}]`
- `limit`: 默认 100
- `offset`: 默认 1
- `queryResultType`: `SQL_AND_DATA`（默认）/ `SQL` / `DATA`

## Output Specification

### Output Structure

输出分为 3 个部分，顺序固定，缺一不可（铁律 0）：

1. **📊 查询解读** — 自然语言，面向业务用户，解释查了什么
   - 用一段连贯的话描述（不用列表）
   - 必须涵盖：指标（中文名+英文代码+口径）、时间范围（具体日期）、维度（中文名+英文代码）、筛选条件、计算方式
   - 简单查询 1-2 句，复杂查询可多几句

2. **📋 查询请求 JSON** — 格式化缩进的完整 JSON，与实际发送的一致

3. **📈 查询结果** — 数据表格，列名使用中文展示名

### Translation Rules

| 技术对象 | 翻译为 | 示例 |
|----------|--------|------|
| timeConstraint（NOW() 相对表达式） | 具体日期/月份 | `DATEADD(DateTrunc(NOW(), "MONTH"), -1, "MONTH")` → "上月（2026年2月）" |
| 快速计算后缀 | 业务语言 | `__sameperiod__mom__growth` → "月环比增长率，即(本月-上月)/上月" |
| metricDefinitions (period+expr) | 计算逻辑 | `grain_to_date 0 year of 0 day` → "本年至今累计" |
| filters / resultFilters | 中文维度名+值 | `[first_channel]= "Wholesale"` → "一级渠道为 Wholesale" |
| resultFilters 额外说明 | 标注"不影响计算" | → "只过滤展示结果，不影响占比/排名计算" |

## Examples

### 示例 1: 基础查询（简单）

**用户说**: "上月的销售额是多少？"

```json
{
    "metrics": ["retail_amt"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")"
}
```

**要点**: 最简查询，dimensions 为空表示查总量。

### 示例 2: 同环比 + 排名 TOP-N（中等）

**用户说**: "上月各渠道的销售额及月环比增长率，增速前5名"

```json
{
    "metrics": ["retail_amt", "retail_amt__sameperiod__mom__growth"],
    "dimensions": ["first_channel"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")",
    "orders": [{"retail_amt__sameperiod__mom__growth": "desc"}],
    "limit": 5
}
```

**要点**: 简单同环比，单次快速计算，无需 metricDefinitions。

### 示例 3: 全局占比 + resultFilters（中等，易错）

**用户说**: "上月 Wholesale 渠道的销售额全局占比"

```json
{
    "metrics": ["retail_amt", "retail_amt__proportion__"],
    "dimensions": ["first_channel"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")",
    "resultFilters": ["[first_channel]= \"Wholesale\""]
}
```

**要点**: 铁律 3 — 用 resultFilters 而非 filters，否则占比恒 100%。

### 示例 4: 跨时间段对比（复杂）

**用户说**: "2025年5月 vs 2月各渠道的销售额增幅"

```json
{
    "metrics": ["may_val", "feb_val", "growth_rate"],
    "metricDefinitions": {
        "may_val": { "refMetric": "retail_amt", "period": "relative_date 0 month of 0 month" },
        "feb_val": { "refMetric": "retail_amt", "period": "relative_date -3 month of 0 month" },
        "growth_rate": { "expr": "([may_val]-[feb_val])/[feb_val]" }
    },
    "dimensions": ["first_channel"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = \"2025-05-01\"",
    "orders": [{"growth_rate": "desc"}]
}
```

**要点**: period + timeConstraint 配合；字面日期因为用户指定了具体月份。

### 示例 5: 日均 + 年同比（复杂，preAggs 手动拆分）

**用户说**: "本年至今的日均销售额及年同比"

```json
{
    "metrics": ["ytd_daily_avg", "ly_ytd_daily_avg", "yoy_growth"],
    "metricDefinitions": {
        "ytd_daily_avg": {
            "refMetric": "retail_amt",
            "period": "grain_to_date 0 year of 0 day",
            "preAggs": [{"granularity": "DAY", "calculateType": "AVG"}]
        },
        "ly_ytd_daily_avg": {
            "refMetric": "retail_amt",
            "period": "grain_to_date -1 year of -1 day",
            "preAggs": [{"granularity": "DAY", "calculateType": "AVG"}]
        },
        "yoy_growth": {
            "expr": "([ytd_daily_avg]-[ly_ytd_daily_avg])/[ly_ytd_daily_avg]"
        }
    },
    "timeConstraint": "['metric_time__day']= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"DAY\")"
}
```

**要点**: preAggs + 同比不能叠加 indirections，必须分两步 + expr（组合约束）。

### 示例 6: 环比增速 + 排名分步（边界，铁律5 高频违反）

**用户说**: "上月各渠道销售额环比增速前3的品牌"

```json
{
    "metrics": ["retail_amt", "mom_growth", "mom_growth__rankDense__desc__first_channel"],
    "metricDefinitions": {
        "mom_growth": {
            "refMetric": "retail_amt",
            "indirections": ["sameperiod__mom__growth"]
        }
    },
    "dimensions": ["first_channel", "product_brand_name"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")",
    "resultFilters": ["[mom_growth__rankDense__desc__first_channel] <= 3"],
    "orders": [{"first_channel": "asc"}, {"mom_growth__rankDense__desc__first_channel": "asc"}]
}
```

**要点**: 先定义环比临时指标，再对它做排名。链式 `retail_amt__sameperiod__mom__growth__rankDense__desc__` 违反铁律5。

### 示例 7: MetricMatches 跨指标筛选（复杂）

**用户说**: "上月销售额≥1万的客户有多少"

```json
{
    "metrics": ["filtered_cnt"],
    "metricDefinitions": {
        "filtered_cnt": {
            "refMetric": "buyer_cnt",
            "filters": ["MetricMatches([vip_code], [retail_amt] >= 10000)"]
        }
    },
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")"
}
```

**要点**: MetricMatches 只能在 metricDefinitions 的 filters 中（铁律6）。

### 示例 8: 非时间维度多层聚合 — "店均"（中等）

**用户说**: "上季度的店均销售额"

```json
{
    "metrics": ["avg_per_store"],
    "metricDefinitions": {
        "avg_per_store": {
            "refMetric": "retail_amt",
            "indirections": ["multi_level_agg__avg,store_code"]
        }
    },
    "timeConstraint": "DateTrunc(['metric_time'], \"QUARTER\") = DATEADD(DateTrunc(NOW(), \"QUARTER\"), -1, \"QUARTER\")"
}
```

**要点**: "XX均"用 multi_level_agg，不要误用 dimensions 展开。

## Error Patterns

### ❌ 模式 1: 占比恒为 100%
**现象**: proportion 结果全为 100%
**原因**: filters 在占比计算前过滤数据，分母只剩自身；或范围维度覆盖了所有非日期维度
**对应规则**: 规则 3
**正确做法**: 用 resultFilters 做展示筛选

### ❌ 模式 2: 排名恒为 1
**现象**: rank 结果全为 1
**原因**: 同模式 1
**对应规则**: 规则 3

### ❌ 模式 3: 硬编码日期替代 NOW()
**现象**: timeConstraint 出现字面日期如 `'2026-03-05'`
**原因**: 相对时间表达误用字面日期
**对应规则**: 规则 1

### ❌ 模式 4: 临时指标未加入 metrics
**现象**: 临时指标在结果中缺失
**原因**: metricDefinitions 中定义了但未在 metrics 注册
**对应规则**: 规则 2

### ❌ 模式 5: 时间条件放在 filters
**现象**: 时间过滤不生效
**原因**: 时间筛选应放 timeConstraint，不应放 filters
**对应规则**: Filter Routing

### ❌ 模式 6: MetricMatches 放在顶层 filters
**现象**: 查询报错
**原因**: 顶层 filters 不支持 MetricMatches
**对应规则**: 规则 6

### ❌ 模式 7: 链式快速计算
**现象**: 语法错误或意外结果
**原因**: 同环比+排名链式叠加
**对应规则**: 规则 5

### ❌ 模式 8: 占比缺少分组维度
**现象**: dimensions 为空但使用 proportion__
**原因**: 无分组维度，系统无法计算占比
**对应规则**: 占比前提条件

### ❌ 模式 9: 粒度后缀大小写错误
**现象**: `metric_time__DAY` 导致报错或空结果
**原因**: 粒度后缀必须全部小写
**正确做法**: `metric_time__day`

### ❌ 模式 10: 非查询消息生成无效请求体
**现象**: "你好"生成空 metrics 请求体
**对应规则**: 规则 9 检查 C
**正确做法**: 返回空 JSON `{}`

### ❌ 模式 11: 幻觉指标
**现象**: 使用工具返回结果之外的指标名
**对应规则**: 规则 9 检查 A

### ❌ 模式 12: 维度不兼容
**现象**: 使用指标不支持的维度
**对应规则**: 规则 9 检查 B

### ❌ 模式 13: timeConstraint + period 双重偏移
**现象**: 查询的是"上上期"而非预期时段
**原因**: timeConstraint 已偏移到目标，period 又额外偏移
**正确做法**: timeConstraint 锚定基准，period 从基准偏移到目标

### ❌ 模式 14: 临时指标命名冲突
**现象**: 查询行为不可预测
**正确做法**: 临时指标名加业务前缀/后缀

### ❌ 模式 15: 累计指标当当期指标
**现象**: 趋势值逐月递增
**原因**: 用了"至今累计"类派生指标做月度趋势
**正确做法**: 趋势场景用原始指标 + 时间粒度维度

### ❌ 模式 16: preAggs 时 dimensions 含同粒度时间维度
**现象**: 日均等于原值
**原因**: preAggs 按 DAY 聚合但 dimensions 有 metric_time__day
**正确做法**: preAggs 聚合粒度不应与 dimensions 时间粒度相同

### ❌ 模式 17: 多指标查询未校验维度兼容性
**现象**: 查询报错或返回空
**正确做法**: 多指标时取维度交集

### ❌ 模式 18: 维度值大小写/格式不匹配
**现象**: filters 无效
**正确做法**: 严格按工具返回的维度值样本原始写法

### ❌ 模式 19: 用户问总量却添加了不必要的 dimensions
**现象**: 返回明细而非总数
**正确做法**: "上月销售额是多少" → dimensions 为空

### ❌ 模式 20: "日均"误用 metric_time__day 替代 preAggs
**现象**: 返回每天的值而非日均
**正确做法**: 用 metricDefinitions + period + preAggs

### ❌ 模式 21: 排名/TOP-N 按错误指标排序
**现象**: 排序结果不符合用户预期
**正确做法**: 排序指标必须与用户关注的指标一致
