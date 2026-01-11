# Change: 新增“涩情元素”独立分析（并行 LLM call + 新 Tab）

## Why

当前系统把“雷点（deal-breakers）”作为一个分析模块，但用户希望将部分并非雷点、而是“偏好/标签”的内容单独列出，避免把喜好与劝退项混在同一模块里。

本变更要解决：
- 在不改变现有“雷点”能力的前提下，新增一个并行的“涩情元素”分析，用于展示特定类型的色情元素标签（不算雷点）。
- 同时补全/明确“雷点”模块的类型覆盖（新增强奸/迷奸、重口/血腥调教等），并保留现有 NTR/恶堕 等类型。

## What Changes

- 新增（ADD）一个独立的 LLM section：`lewd_elements`
  - 独立 prompt（Jinja2）与 tool_name
  - 独立 Pydantic 输出 schema
  - 独立 API：`POST /api/analyze/lewd-elements`
  - 与现有 `scenes`/`thunder` 并行请求（不改现有端点）

- 新增（ADD）一个前端 Tab：“涩情元素”
  - 分析完成后可用（与其他分析 tab 一致）
  - 展示 4 类标签：`乱伦`（直系+旁系合并）、`调教`、`恋足`（臭脚并入）、`萝莉`
  - 每类最多 1 条：只要“存在 + 1 个代表性实例”（可带章节/角色）
  - “萝莉”口径更严格：仅在文本存在明确未成年/低龄证据时才标注

- 修改（MOD）“雷点”类型覆盖
  - 保留：`绿帽`、`NTR`、`恶堕`、`其他`
  - 补充：`强奸/迷奸`、`重口/血腥调教`
  - 目标是覆盖用户关注的核心雷点范围，同时不把“调教/恋足/乱伦/萝莉”当作雷点（它们转为“涩情元素”）

- 新增/更新测试（Tests）
  - 新增“涩情元素”渲染单测与 E2E 覆盖
  - 更新现有 stub / fixtures 以支持新端点并确保导出一致

## Impact

- **Affected specs**:
  - `lewd-elements`（新增 capability）
  - `thunderzones`（新增/完善现有能力的规范化描述）
  - 说明：当前存在活跃变更 `simplify-tab-interaction`（涉及 tab 列表与启用逻辑）。本变更也会新增一个 tab，实施时需要与该变更协调/合并。

- **Affected code**（预期）：
  - 后端：`backend.py`、`src/novel_analyzer/schemas.py`、`src/novel_analyzer/validators.py`
  - 配置与 prompts：`config/llm.yaml`、`config/prompts/lewd_elements.j2`、`config/prompts/thunder.j2`
  - 前端：`templates/index.html`、`static/chart-view.js`、`static/style.css`（如需）
  - 测试：`tests/test_*`（新增/更新单测与 E2E）

- **Breaking changes**: 无（新增字段/端点；原有雷点端点保持不变）。
- **Risks / trade-offs**:
  - 新增一次 LLM 调用会增加成本与并行负载；但可与现有 `scenes`/`thunder` 并行，尽量降低用户等待时间。
  - 分析结果对象新增字段，需要确保前端对缺失字段（旧缓存）具备兼容性。
