## Context

当前分析流水线包含：`meta`、`core`、并行执行的 `scenes` 与 `thunder`。其中 `thunder` 用于输出“雷点（deal-breakers）”，并通过 Pydantic schema + 一致性校验保证结构化输出。

用户希望将部分“非雷点但属于色情元素/偏好标签”的内容独立出来，避免与雷点混淆，同时补全 thunder 的雷点类型覆盖。

## Goals / Non-Goals

### Goals
- 新增“涩情元素”作为独立一次 LLM 调用（与 thunder 并行），并在 UI 新增独立 Tab 展示。
- “涩情元素”只输出 4 类（乱伦/调教/恋足/萝莉），每类最多 1 条示例（存在即列出）。
- “萝莉”使用严格口径（仅明确未成年/低龄证据时才标注）。
- 保持现有 “雷点” 能力（thunderzones）端点与输出结构不变，同时更新/补全其类型覆盖。

### Non-Goals
- 不在本变更中引入“男主/女主”自动识别或额外角色标注字段。
- 不把“涩情元素”并入雷点 schema（不使用 severity 来表达喜好）。
- 不改变现有 LLM 客户端调用方式（仍为 Function Calling + Pydantic 校验 + 可选 repair pass）。

## Decisions

### 1) 新增 section：`lewd_elements`
- 在 `config/llm.yaml` 增加 `sections.lewd_elements`，配置独立 `tool_name` 与 prompt。
- 后端新增 `POST /api/analyze/lewd-elements`，请求体与 `thunderzones/scenes` 一致（`content + characters + relationships`），便于复用角色名约束。
- 与 `scenes`/`thunder` 并行执行，降低总等待时间。

### 2) 输出结构：只输出“存在的类型”，每类最多 1 条
- `lewd_elements` 采用列表结构（与现有 thunderzones 风格一致），每个元素包含：
  - `type`（固定集合：乱伦/调教/恋足/萝莉）
  - `example`（非空：给 1 个代表性实例即可）
  - 可选：`chapter_location`、`involved_characters`
- 约束：同一 `type` 不得重复出现（可在 validator 中校验）。

### 3) “萝莉”严格口径
- Prompt 明确要求：只有在文本出现明确未成年/低龄证据（如 <18、未成年、小学生/初中生等清晰表述）时才输出 `type=萝莉`。
- “幼态/娇小/萝莉风”但无明确未成年信息时不得输出该类型。

### 4) 雷点类型覆盖补全，但不把偏好当雷点
- 更新 thunder prompt：保留现有类型（绿帽/NTR/恶堕/其他），并补充强奸/迷奸、重口/血腥调教（合并为一个雷点类别）。
- 约束：正常“调教/SM”、恋足、乱伦、萝莉不作为雷点输出（改由 lewd_elements 输出）。

### 5) 前端与导出
- UI 新增 Tab “涩情元素”，分析完成后可用，展示 summary + 元素卡片。
- 导出报告保持与 UI 一致：导出 HTML 包含“涩情元素”模块，且对缺失字段（旧缓存）有降级处理。

## Alternatives Considered
- 将涩情元素合并进 thunder（单次 LLM call）：被拒绝，因为会混淆“雷点”与“标签/偏好”。
- 使用 thunder 的 severity=低 表达“喜欢”：被拒绝，因为语义不匹配且影响排序/视觉。
- 使用固定对象结构（4 个字段而非列表）：可行但扩展性较差；本次优先保持与 thunderzones 一致的 list 结构。

## Risks / Trade-offs
- 成本：新增一次 LLM 调用。
- 一致性：需要处理旧缓存数据缺失新字段的场景。
- 变更冲突：`templates/index.html` 的 tabs 结构与活跃变更 `simplify-tab-interaction` 可能冲突，需要实施时合并。

## Migration Plan
- 新字段为可选（前端渲染对缺失字段降级到空态）。
- 端点新增，不影响旧客户端。
