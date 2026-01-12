# 实施任务清单

## 1. OpenSpec / 需求对齐
- [ ] 1.1 运行 `openspec validate add-lewd-elements-analysis --strict`
- [ ] 1.2 与活跃变更 `simplify-tab-interaction` 协调 tabs 结构改动点，确认合并策略

## 2. 后端：新增涩情元素分析端点
- [ ] 2.1 在 `config/llm.yaml` 新增 `sections.lewd_elements`（tool_name + prompt_file + temperature）
- [ ] 2.2 新增 prompt 模板 `config/prompts/lewd_elements.j2`
  - 类型集合：乱伦/调教/恋足/萝莉
  - 每类最多 1 条示例
  - 萝莉严格口径（无明确未成年证据不得输出）
- [ ] 2.3 在 `src/novel_analyzer/schemas.py` 增加 `LewdElementEntry` / `LewdElementsOutput`
- [ ] 2.4 在 `src/novel_analyzer/validators.py` 增加一致性校验
  - type 只能是允许集合
  - 同 type 不重复
  - involved_characters（若提供）必须在 allowed_names 中
- [ ] 2.5 在 `backend.py` 新增 `POST /api/analyze/lewd-elements`
  - 请求体沿用 `content + characters + relationships`
  - 复用 content 截断与 prompt 渲染
  - 输出 `{ "analysis": LewdElementsOutput }`

## 3. 后端：补全雷点类型覆盖
- [ ] 3.1 更新 `config/prompts/thunder.j2` 的类型列表与说明
  - 增补：强奸/迷奸、重口/血腥调教
  - 保留：绿帽、NTR、恶堕、其他
  - 明确：调教/恋足/乱伦/萝莉不作为雷点

## 4. 前端：新增 Tab 与渲染
- [ ] 4.1 在 `templates/index.html` 的 tabs 数组新增 `{ id: "lewd-elements", name: "涩情元素" }`
- [ ] 4.2 在 `templates/index.html` 增加对应容器（例如 `#lewdElementsSection`）
- [ ] 4.3 在分析流程中并行请求新端点
  - 与 scenes/thunder 同级 Promise.all
  - 合并到最终 analysis 对象中，供渲染与导出使用
- [ ] 4.4 在 `static/chart-view.js` 增加 `renderLewdElements` + `buildLewdElementsHtml`
  - 空态：未检测到相关元素
  - 每类卡片：类型 + 示例 + 可选章节/角色
- [ ] 4.5 更新导出 `exportReport(...)`：包含“涩情元素”模块，且与网页渲染一致

## 5. 测试
- [ ] 5.1 新增/更新单测：验证 `buildLewdElementsHtml` 空态与有数据渲染
- [ ] 5.2 更新 E2E stub：支持 `/api/analyze/lewd-elements` 返回
- [ ] 5.3 新增 E2E：
  - Tab 可见
  - 空态文案
  - 有数据时至少渲染一类卡片
  - 导出报告中包含涩情元素模块

## 6. 验证
- [ ] 6.1 运行 `.\venv\Scripts\python.exe -m pytest -q`
- [ ] 6.2 运行 `.\venv\Scripts\python.exe -m compileall backend.py src/novel_analyzer`
- [ ] 6.3 再次运行 `openspec validate add-lewd-elements-analysis --strict`
