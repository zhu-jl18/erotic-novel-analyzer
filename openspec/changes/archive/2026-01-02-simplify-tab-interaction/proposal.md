# Change: 简化 Tab 交互逻辑，移除冗余卡片和多余的始终可用 Tab

## Why

当前 UI 交互存在冗余和困惑：
1. "已选择小说"卡片在所有 tab（进度/总结/日志/调试）中重复显示，造成视觉噪音
2. "总结" tab 设置为始终可用（`alwaysEnabled: true`），但分析前点击该 tab 只能看到重复的卡片和空内容，用户体验差
3. 用户困惑：为什么"总结" tab 能点击但什么都没有?

## What Changes

- 限制"已选择小说"卡片仅在"进度" tab 显示（添加 tab 条件判断）
- 移除"总结" tab 的 `alwaysEnabled` 属性，使其与"雷点"、"角色"等其他分析 tab 行为一致（分析完成后才可用）
- 保留"日志" tab 的 `alwaysEnabled: true`（日志有独立价值，用于调试和操作追踪）
- 保留"调试" tab 的 `alwaysEnabled: true`（用于查看 LLM dumps，有独立调试价值）

优化后的交互流程：
- 选择小说后，只有"进度"、"日志"、"调试"三个 tab 可用
- "总结"等分析 tab 显示禁用样式（40% 不透明度），引导用户先点击"开始分析"
- 分析完成后，自动切换到"总结" tab，所有分析 tab 变为可用

## Impact

- **Affected specs**: `ui-interaction-flow`（新建 capability）
- **Affected code**:
  - `templates/index.html:177` - "已选择小说"卡片的 `x-show` 条件
  - `templates/index.html:590` - tabs 数组中"总结" tab 的定义
- **New tests required**: `tests/test_tab_interaction_e2e.py`（新建）
  - 验证选择小说后的 tab 禁用状态
  - 验证"已选择小说"卡片只在"进度" tab 显示
  - 验证分析完成后的 tab 状态和自动切换
  - 验证分析完成后卡片不再显示
- **Existing tests**: 无影响（现有 E2E 测试都在分析完成后操作 tab，不受此改动影响）
- **Breaking changes**: 无（仅优化交互逻辑，不影响数据或 API）
- **User impact**: 更清晰的交互引导，减少困惑
