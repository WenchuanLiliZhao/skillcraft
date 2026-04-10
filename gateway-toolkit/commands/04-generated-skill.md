---
name: metric-query
description: |
  根据用户自然语言描述，通过语义层 API 查询指标数据。数据查询通过 搜索指标 / 查询维度 / 执行查询 三个工具完成。
  触发场景包括但不限于：用户提到"查询指标""指标数据""同环比""占比""排名""时间限定""销售额""客单价""趋势""日均""对比"等关键词。
  **重要：构建查询前，必须先检索相关指标和维度信息，禁止凭记忆猜测指标名或维度名。**
---

# 指标数据查询 Skill

根据用户自然语言描述，通过语义层 API 查询指标数据。

## 接口信息

### 搜索指标 (`search_metrics`)

调用 **search_metrics** 工具：
- 参数：
  - `keyword` (string, 必填): 搜索关键词，支持逗号分隔批量搜索
  - `pageSize` (number, 选填): 每个关键词返回数量，默认 5

认证由工具内部处理，无需手动传递 API Key。

示例：
- 单个关键词：调用 **search_metrics** 工具：`keyword: "客单价"`, `pageSize: 5`
- 批量搜索：调用 **search_metrics** 工具：`keyword: "客单价,销售额"`, `pageSize: 3`

返回纯文本，每行一个指标：
```
[客单价] 3 metric(s):
- AOV | 客单价 | 销售金额/购买客户数 (53 dims)
- l7d_AOV | 近7天客单价 [DERIVED] (53 dims)
```

返回解析规则:
- 行首英文名（如 `AOV`）= metricName → 放入 `metrics` 数组
- `|` 后第一段 = displayName（中文展示名）→ 用于查询解读
- `|` 后第二段 = description（业务口径）→ 用于查询解读
- `[DERIVED]` = 派生指标，使用前必须验证其语义与用户意图完全一致

⚠️ 保存元数据：metricName、displayName、description 供查询解读使用。

### 查询维度 (`get_dimensions`)

调用 **get_dimensions** 工具：
- 参数：
  - `metricNames` (string, 必填): 指标名称，多个用逗号分隔
  - `keyword` (string, 选填): 过滤关键词，只返回匹配的维度

示例：
- 单指标：调用 **get_dimensions** 工具：`metricNames: "AOV"`
- 单指标 + keyword 过滤：调用 **get_dimensions** 工具：`metricNames: "AOV"`, `keyword: "渠道"`
- 批量（自动算交集）：调用 **get_dimensions** 工具：`metricNames: "AOV,retail_amt"`, `keyword: "渠道"`

单指标返回格式：
```
Metric '客单价' (AOV), 53 dimension(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale
- gender(性别): 女, 男
```

批量返回格式（含维度交集）：
```
## 客单价 (AOV), 2 dim(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale

## COMMON dimensions (intersection), 2 dim(s):
- first_channel(一级渠道): Direct, E-commerce, Retail, Wholesale
```

返回解析规则:
- 行首英文名（如 `first_channel`）= dimName → 放入 `dimensions` / `filters`
- 括号内（如 `一级渠道`）= displayName → 用于查询解读
- 冒号后 = 维度值样本 → 用于 filters/resultFilters 值匹配（必须严格按原始写法）
- `COMMON dimensions` = 多指标共有维度交集 → 多指标查询时 dimensions 只能从这里选
- `metric_time` 是所有指标的默认可分析维度，支持粒度后缀：`__day`, `__month`, `__year`, `__week`, `__quarter`

⚠️ 优先使用 keyword 过滤。多指标查询必须用批量方式（逗号分隔 metricNames），一次拿到交集。

### 执行查询 (`query_metrics`)

调用 **query_metrics** 工具，参数 `requestBody` 为完整的 JSON 请求体字符串。

示例：
调用 **query_metrics** 工具：`requestBody: '{"metrics": ["AOV"], "timeConstraint": "[\'metric_time__day\']= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"DAY\")"}'`

---

## ⚡ 十条铁律（违反任何一条 = 错误）

> 构建请求前，先逐条过一遍：

### 铁律 0 — 每次查询必须输出「📊 查询解读」，且必须放在 JSON 之前

向用户展示时，必须先输出查询解读（自然语言解释），然后是请求 JSON，最后是查询结果。三段缺一不可，顺序不可颠倒。

✅ 正确: 📊 查询解读 → 📋 请求 JSON → 📈 查询结果
❌ 错误: 直接展示 JSON 或结果，跳过查询解读

### 铁律 1 — 相对时间必须用 NOW()，禁止硬编码日期（包括 timeConstraint 和 period 锚定）

"上月""昨天""近N天"等相对时间表达 → 必须用 `NOW()` 函数。

✅ `DATEADD(DateTrunc(NOW(), "MONTH"), -1, "MONTH")`
❌ `DATEADD(DateTrunc('2026-03-05', "MONTH"), -1, "MONTH")`

⚠️ 特别注意：period 锚定的 timeConstraint 也必须用 NOW()。锚定日期用 `DATEADD(DateTrunc(NOW(), "DAY"), -1, "DAY")` 表示昨天，不可将当前日期硬编码。

唯一例外：用户明确说了 "2025年4月" 这样的具体日期 → 才可用字面日期。

### 铁律 2 — metricDefinitions 中每个 key 必须同时在 metrics 数组中（包括辅助指标）

定义了临时指标就必须注册到 `metrics`。包括仅作为 `expr` 中间计算变量的辅助指标。

✅ `"metrics": ["total", "ratio"]` + `"metricDefinitions": { "total": {...}, "ratio": { "expr": "[val]/[total]" } }`
❌ `"metrics": ["ratio"]` + `"metricDefinitions": { "total": {...}, "ratio": { "expr": "[val]/[total]" } }`（total 未注册）

### 铁律 3 — 占比/排名 + filters = 分母/范围被缩小 → 结果恒 100%/恒为 1

要"某个值在全局中的占比/排名" → 用 `resultFilters` 做展示筛选，不用 `filters`。

⚠️ "Wholesale 渠道的占比"含义是 Wholesale 在所有渠道中的占比。dimensions 必须包含渠道维度，用 resultFilters 仅展示 Wholesale 行。

✅ `"resultFilters": ["[first_channel]= \"Wholesale\""]` → 分母包含所有渠道
❌ `"filters": ["[first_channel]= \"Wholesale\""]` → 只剩 Wholesale 自己，占比恒 100%

### 铁律 4 — "同比"默认 = yoy；带粒度前缀时按前缀选择

| 用户说 | 映射 |
|--------|------|
| "同比"（无限定）/ "年同比" | yoy |
| "月同比" | mom |
| "周同比" | wow |
| "季同比" | qoq |

⚠️ 中文"同比"单独出现时，一律映射为 yoy。

### 铁律 5 — 一个指标只能做一次快速计算，不可链式叠加

需要多步（如先算环比再排名）→ 用 `metricDefinitions` 分步。

✅ 先定义 `mom_growth` 临时指标，再对它做 `mom_growth__rankDense__desc__first_channel`
❌ `retail_amt__sameperiod__mom__growth__rank__desc__first_channel`（链式叠加）

### 铁律 6 — MetricMatches 只能在 metricDefinitions 的 filters 中使用，禁止放在顶层 filters

✅ `"metricDefinitions": { "temp": { "filters": ["MetricMatches(...)"] } }`
❌ `"filters": ["MetricMatches(...)"]`（顶层 filters 不支持）

### 铁律 7 — 派生指标的 metric_time 粒度限制必须遵守

标注"仅支持日粒度"的派生指标，只能在 timeConstraint 锚定到天粒度时使用。

✅ 上月销售额同比 → `retail_amt__sameperiod__yoy__growth`（原子指标+快速计算）
❌ 上月销售额同比 → `sales_yoy`（日粒度派生指标 + 月级 timeConstraint = 不兼容）

### 铁律 8 — "月变化趋势"中的占比/排名范围维度必须是 metric_time__month

✅ `retail_amt__proportion__metric_time__month`（每月内各渠道占比）
❌ `retail_amt__proportion__`（全局占比，无月内分组 → 跨月混淆）
❌ `retail_amt__proportion__first_channel`（每渠道内占比 → 恒100%）

### 铁律 9 — 上下文不足时必须拒绝生成查询，返回空 JSON {}

生成 JSON 前，必须通过以下三项检查，任一不通过则拒绝：
- **检查 A**: 候选指标能否覆盖用户需求？（无 → 禁止虚构指标名）
- **检查 B**: 所选维度是否在指标的可分析维度内？（不在 → 禁止使用）
- **检查 C**: 用户消息是否包含查询意图？（纯问候 → 返回空 JSON）

---

## 语义理解（构建前必做）

### 分解维度

在写任何 JSON 之前，先把用户的问题拆解为四个维度：

| 维度 | 核心问题 | 对应 API 参数 | 示例 |
|------|----------|-------------|------|
| 看什么（指标） | 用户要看的业务量是什么？ | `metrics` | "销售额""客单价""日均订单数" |
| 怎么看（分析方式） | 直接看值？对比？占比？排名？ | 快速计算后缀 / `metricDefinitions` | "同比增长率""占比""排名前5" |
| 看谁的（维度&筛选） | 按什么拆分？筛选哪些？ | `dimensions` / `filters` / `resultFilters` | "各品牌""某渠道""某地区" |
| 看哪段时间 | 时间范围？时间对比？ | `timeConstraint` | "上月""近7天""某月vs另一月" |

### 关键语义消歧

规则 A — "总和" vs "分别"：
| 用户说 | 含义 | dimensions 处理 |
|--------|------|----------------|
| "A 和 B 的指标分别是多少" | 按 A、B 分组展示 | 保留维度 |
| "A 和 B 的指标总和" | 合并为一个数字 | 不放该维度 |
| "A 和 B 的指标"（无修饰） | 歧义，默认"分别" | 保留维度 |

规则 B — 修饰语的作用域：
"日均/月均/平均"修饰紧跟其后的所有并列项。

规则 C — "占比"的两种含义：
- "销售额占比"（值占比）→ 直接用 `proportion` 快速计算
- "款色占比""客户占比"（数量占比）→ 先用计数指标统计数量，再对计数指标做 `proportion`
- 判断标准：占比前面是实体类型 → 数量占比；是指标名 → 值占比

规则 D — "XX均"的聚合维度：
"XX均"中的"XX"就是聚合维度 → `multi_level_agg__avg,{XX对应的维度名}`

规则 E — "同比" vs "环比"：
- "同比"（无限定）→ yoy（默认=年同比，详见铁律 4）
- "环比" → 按时间粒度选：日→dod，周→wow，月→mom，季→qoq

规则 F — "对比去年末" ≠ "年同比"：
- "同比" → `__sameperiod__yoy__growth`
- "与去年末相比" → `metricDefinitions + period` 定位去年末（如 `SPECIFY_DATE end day of -1 year`）

规则 G — "趋势" ≠ 同环比：
"趋势"/"变化趋势" = 按时间展开看值的变化。除非用户明确提到"同比""环比"，否则不要额外添加。

规则 H — "差异/差距/对比" ≠ 同环比：
"各XX之间的差异" = 直接查出各自的值让用户比较，不是同比/环比。

规则 I — 简单优先：
如果用户问题可以用简单查询回答，就不要添加不必要的 metricDefinitions、同环比、占比、排名。

规则 J — 无年份日期默认当年：
用户提到日期但未指定年份时，默认指当前年份。参考 system prompt 中的 Current date。

---

## JSON 格式规范

请求体为标准 JSON。所有字符串值内部的双引号必须转义为 `\"`。
```json
"filters": ["[dim_A]= \"value_1\""]
"timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\""
```

## 请求参数

### metrics（必填）— 指标列表

```json
"metrics": ["metric_A", "metric_B"]
```

快速计算后缀（每个指标只能应用一次，铁律 5）：

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
| 增长了多少/增长率/增速 | growth | (当前 − 对比) / 对比 |
| 下降了多少 | decrease | 对比 − 当前 |
| 下降率 | decreaserate | (对比 − 当前) / 对比 |

约束: `metric_time` 须在 `dimensions` 或 `timeConstraint` 中出现；偏移粒度不可小于 `metric_time` 粒度；期末/期初偏移仅 metric_time__day 粒度可用。

**占比**: `{指标}__proportion__{范围维度}`
| 范围维度写法 | 分母 |
|-------------|------|
| `proportion__`（末尾两个下划线） | 全部数据汇总（全局占比） |
| `proportion__dim_A` | 按 dim_A 每组分别汇总（组内占比） |

前提: dimensions 必须包含参与占比计算的实体维度。
⚠️ 陷阱一 — 恒为 100%: 范围维度覆盖 dimensions 中所有非日期维度时，占比恒为 100%。
⚠️ 陷阱二 — filters 缩小分母: filters 在占比计算前过滤。用 resultFilters 做展示筛选。

**排名**: `{指标}__{方式}__{顺序}__{范围维度}`
- 方式: `rank`（并列跳号）/ `rankDense`（并列不跳）/ `rowNumber`（不并列）
- 顺序: `desc`（大=1）/ `asc`（小=1）
- 范围维度: 省略=全局；填维度=组内排名
- 陷阱与占比完全相同。

**时间限定**: `{指标}__period__{限定}`
| 类型 | 语法示例 |
|------|---------|
| 近N期 | 7d, 3w, 6m, 2q, 1y |
| 本期至今 | ytd, qtd, mtd, wtd |
| 当前期间 | cy, cq, cm, cw, cd |

### metricDefinitions（选填）— 临时指标定义

⚠️ 核心规则（铁律 2）— 必须双重注册: 每个 key 都必须同时出现在 metrics 数组中。

临时指标命名: 必须与所有已有指标名称不同。

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

period 与 timeConstraint 配合:
- timeConstraint 锚定到天 → period 用 `of 0 day`
- timeConstraint 锚定到月 → period 用 `of 0 month`
- of 后粒度不可细于 timeConstraint 锚定粒度

**preAggs**: `[{"granularity": "DAY", "calculateType": "AVG"}]`
- granularity: DAY / WEEK / MONTH / QUARTER / YEAR
- calculateType: AVG / MAX / MIN
- 典型场景: "近30天日均" = period 限定30天 + preAggs 按 DAY 求 AVG
- ⚠️ preAggs 聚合粒度不应与 dimensions 时间粒度相同（否则等于没聚合）
- preAggs + 同比: 不能直接叠加 __sameperiod__，须分两步 + expr

**indirections 示例**:
- `["sameperiod__yoy__value"]` → 年同比值
- `["proportion__dim_A"]` → dim_A 组内占比
- `["multi_level_agg__avg,dim_A"]` → 非时间维度多层聚合

period + indirections 组合（推荐）: 不含 preAggs 的 period 指标做同环比 → 用 indirections。含 preAggs 时不可用此组合，须手动分两步 + expr。

multi_level_agg 与外层 dimensions 冲突: 当聚合维度同时在外层 dimensions 中时，结果恒等于自身。必须添加 `specifyDimension: { "type": "EXCLUDE", "dimensions": "dim_X" }`。

**MetricMatches**: `MetricMatches([维度名], [指标名] 运算符 值)`
- 同指标筛选（"指标A≥某值的维度有哪些"）→ resultFilters
- 跨指标筛选（"指标A≥某值的维度有多少个"→ 用 A 筛维度值，再算 B）→ MetricMatches
- 每个 MetricMatches 仅支持一个指标条件，多条件须拆分为多个（数组内为 AND）

### dimensions（选填）— 分析维度

```json
"dimensions": ["metric_time__month", "dim_A"]
```

⚠️ 粒度后缀必须全部小写: `__day`, `__month`, `__year`, `__week`, `__quarter`。大写会导致查询失败。
⚠️ 维度兼容性: 多指标查询时，dimensions 只能包含所有指标都支持的维度（取交集）。

### filters 与 resultFilters

| | filters | resultFilters |
|---|---------|--------------|
| 等价 SQL | WHERE | HAVING |
| 影响计算 | 是（分母、排名范围都受影响） | 否（仅过滤返回行） |

选择规则:
- 时间相关筛选 → 必须放 `timeConstraint`（⚠️ 禁止放 filters）
- 指标值/计算结果筛选 → `resultFilters`
- 维度值筛选，需影响计算 → `filters`
- 维度值筛选，但不应影响占比/排名 → `resultFilters`

filters 语法: `[dim]= "value"` / `IN([dim], "v1", "v2")` / `NotIn(...)` / `contains(...)` / 数值比较 / 日期比较
resultFilters 语法: `[metric] > 1000` / `[dim]= "value"`

### timeConstraint（选填）— 时间范围

两个角色: A-时间范围过滤（一个区间）；B-period 锚定基准（一个具体日期/月份）。

📋 timeConstraint 速查表:
| 用户说 | timeConstraint |
|--------|---------------|
| 昨天 | `"['metric_time__day']= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"DAY\")"` |
| 今天 | `"['metric_time__day']= DateTrunc(NOW(), \"DAY\")"` |
| 上周 | `"DateTrunc(['metric_time'], \"WEEK\") = DATEADD(DateTrunc(NOW(), \"WEEK\"), -1, \"WEEK\")"` |
| 本周 | `"DateTrunc(['metric_time'], \"WEEK\") = DateTrunc(NOW(), \"WEEK\")"` |
| 上月 | `"DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")"` |
| 本月 | `"DateTrunc(['metric_time'], \"MONTH\") = DateTrunc(NOW(), \"MONTH\")"` |
| 上季 | `"DateTrunc(['metric_time'], \"QUARTER\") = DATEADD(DateTrunc(NOW(), \"QUARTER\"), -1, \"QUARTER\")"` |
| 本季 | `"DateTrunc(['metric_time'], \"QUARTER\") = DateTrunc(NOW(), \"QUARTER\")"` |
| 本年 | `"DateTrunc(['metric_time'], \"YEAR\") = DateTrunc(NOW(), \"YEAR\")"` |
| 去年 | `"DateTrunc(['metric_time'], \"YEAR\") = DATEADD(DateTrunc(NOW(), \"YEAR\"), -1, \"YEAR\")"` |
| 近7天 | `"DateTrunc(['metric_time'], \"DAY\") >= DATEADD(DateTrunc(NOW(), \"DAY\"), -7, \"DAY\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")"` |
| 近30天 | `"DateTrunc(['metric_time'], \"DAY\") >= DATEADD(DateTrunc(NOW(), \"DAY\"), -30, \"DAY\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")"` |
| 近12个月 | `"DateTrunc(['metric_time'], \"MONTH\") >= DATEADD(DateTrunc(NOW(), \"MONTH\"), -12, \"MONTH\") AND DateTrunc(['metric_time'], \"MONTH\") < DateTrunc(NOW(), \"MONTH\")"` |
| 具体月份 | `"DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\""` |
| 具体日期 | `"['metric_time__day']= \"2025-06-15\""` |

⚠️ 表中除最后两行外，全部使用 NOW()（铁律 1）。

**用户未指定时间时的默认策略**（命中第一行即停）:
| 优先级 | 条件 | 默认 timeConstraint |
|--------|------|--------------------|
| 1 | 有 period / __period__ / 时间限定派生指标 | 锚定昨天 |
| 2 | 有 __sameperiod__mom__ | 上月 |
| 3 | 有 __sameperiod__wow__ | 上周 |
| 4 | 有 __sameperiod__qoq__ | 上季 |
| 5 | 有 __sameperiod__yoy__ | 上月 |
| 6 | 有 __sameperiod__dod__ | 昨天 |
| 7 | 有排名/TOP-N 且无时间维度 | 近30天或上月 |
| 8 | dimensions 含 metric_time__month | 近12个月 |
| 9 | dimensions 含 metric_time__quarter | 本年 |
| 10 | dimensions 含 metric_time__week | 近12周 |
| 11 | 其他 | 近7天 |

⚠️ 不可双重偏移: timeConstraint 已限定到某时段时，period 不应再做同方向额外偏移。

### 其他参数

- `orders`: 排序列须在 metrics 或 dimensions 中。格式 `[{"field": "asc/desc"}]`
- `limit`: 默认 100
- `offset`: 默认 1
- `queryResultType`: `SQL_AND_DATA`（默认）/ `SQL` / `DATA`

---

## 构建流程

### 步骤 0：语义解析
按分解维度将用户问题拆解为"看什么/怎么看/看谁的/看哪段时间"，并逐条检查 10 条消歧规则（A~J）。
输出：明确的指标列表、分析方式、维度筛选需求、时间范围。

### 步骤 1：通过工具检索指标
从用户问题中提取核心业务关键词，调用 **search_metrics** 工具搜索指标：`keyword: "{关键词}"`, `pageSize: 10`
从返回结果中取 metricName 放入 metrics 数组。
决策点:
- 有"看似相关"的 DERIVED 指标？→ 验证其 displayName 语义是否与用户意图完全一致
- 用户说了"日均""月均"？→ 按规则 B 判断修饰范围
- 搜索结果为空？→ 更换关键词重试

### 步骤 2：通过工具查询维度 + 兼容性校验
调用 **get_dimensions** 工具获取可用维度：`metricNames: "{metricName}"`（多指标用逗号分隔）
决策点:
- 维度值匹配：通过 sampleValues 判断用户提到的值属于哪个维度
- 维度兼容性：多指标时取交集
- 维度值精确抄写：必须严格按返回的维度值样本原始写法

### 步骤 3：识别快速计算
- 同环比: 按规则 E 选偏移粒度；按规则 F 区分"同比" vs "对比期末"
- 占比: 检查范围维度是否覆盖 dimensions 中所有非日期维度（是 → 恒 100%，需调整）
- 排名: 同上检查恒为 1

### 步骤 4：识别临时指标
跨时段对比、自定义计算、附加业务限定 → 使用 metricDefinitions。
校验: 临时指标名在 metrics 中？不与已有指标重名？period of 后粒度不细于 timeConstraint？preAggs 配合了 period？

### 步骤 5：筛选条件
filters vs resultFilters 决策树:
- 筛选字段是指标值/计算结果？→ resultFilters
- 涉及占比/排名 + 该筛选不应影响分母/范围？→ resultFilters
- 普通维度值筛选 → filters

### 步骤 6：时间范围
按默认策略决策树确定 timeConstraint。校验: 使用 period 时 timeConstraint 是否为具体日期？有无双重偏移？

### 步骤 7：排序分页
排序列须在 metrics 或 dimensions 中。rank 排序用 asc。

### 步骤 8：输出前自检

✅ 输出结构为三段式：📊 查询解读 → 📋 请求 JSON → 📈 查询结果（铁律 0）
✅ 字符串内双引号已用 `\"` 转义
✅ metricDefinitions 中每个 key（含辅助指标）都在 metrics 数组中（铁律 2）
✅ 临时指标名不与已有指标重名
✅ 占比范围维度不会导致恒 100%；排名范围维度不会导致恒为 1（铁律 3）
✅ filters 未不当缩小占比分母/排名范围（全局占比/排名应用 resultFilters）
✅ 同环比偏移粒度匹配用户意图（铁律 4）
✅ period 的 of 后粒度不细于 timeConstraint 锚定粒度
✅ preAggs 格式为数组、配合了 period、且聚合粒度与 dimensions 时间粒度不冲突
✅ timeConstraint 与 period 无双重偏移
✅ 快速计算未链式叠加（铁律 5）
✅ "日均/月均"场景使用了 preAggs（非 dimensions 展开）
✅ 已有派生指标的语义与用户意图完全匹配；日粒度限制的派生指标未在非天粒度 timeConstraint 下使用（铁律 7）
✅ multi_level_agg 聚合维度与外层 dimensions 冲突时，添加了 specifyDimension EXCLUDE
✅ 相对时间使用 NOW()，未硬编码日期（铁律 1）
✅ 每个指标的可用维度都覆盖了 dimensions 中的全部维度（多指标取交集）
✅ 时间过滤条件在 timeConstraint 中，而非 filters 中；MetricMatches 在 metricDefinitions 中（铁律 6）
✅ filters/resultFilters 中的维度值严格匹配工具返回的 sampleValues 原始写法；dimensions/orders 粒度后缀全部小写
✅ 用户要单个汇总数字时无多余维度；"月变化趋势"占比/排名范围维度是 metric_time__month；TOP-N 排序指标正确

---

## 输出展示规范

⚠️ 铁律 0 的执行规范。每次执行指标查询时，必须严格按以下三段式展示，缺一不可，顺序不可颠倒：

1. **📊 查询解读**（自然语言，放在最前面）
   - 用一段连贯的话描述（不用列表）
   - 涵盖：指标（中文名+英文代码+口径）、时间范围（具体日期）、维度（中文名+英文代码）、筛选条件、计算方式
   - 简单查询 1-2 句，复杂查询可多几句

2. **📋 查询请求 JSON**（格式化缩进的完整 JSON，与实际发送的一致）

3. **📈 查询结果**（数据表格，列名使用中文展示名）

翻译规则速查：
| 技术对象 | 翻译为 | 示例 |
|----------|--------|------|
| timeConstraint（NOW() 相对表达式） | 具体日期/月份 | `DATEADD(...)` → "上月（2026年2月）" |
| 快速计算后缀 | 业务语言 | `__sameperiod__mom__growth` → "月环比增长率" |
| metricDefinitions | 计算逻辑 | `grain_to_date 0 year of 0 day` → "本年至今累计" |
| filters/resultFilters | 中文维度名+值 | `[first_channel]= "Wholesale"` → "一级渠道为 Wholesale" |

---

## 完整示例

详见 [references/examples.md](references/examples.md)

## 常见错误模式

详见 [references/error-patterns.md](references/error-patterns.md)
