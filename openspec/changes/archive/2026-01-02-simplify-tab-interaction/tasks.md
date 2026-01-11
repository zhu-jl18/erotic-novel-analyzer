# 实施任务清单

## 1. 前端 UI 逻辑修改

- [x] 1.1 修改"已选择小说"卡片的显示条件
  - 文件：`templates/index.html:177`
  - 修改：将 `x-show="!hasAnyResult()"` 改为 `x-show="currentTab === 'pipeline' && !hasAnyResult()"`
  - 验证：选择小说后切换到"日志" tab，确认卡片不再显示

- [x] 1.2 修改 tabs 数组，移除"总结" tab 的 alwaysEnabled 属性
  - 文件：`templates/index.html:590`
  - 修改：将 `{ id: "summary", name: "总结", alwaysEnabled: true }` 改为 `{ id: "summary", name: "总结" }`
  - 验证：选择小说后，"总结" tab 显示禁用样式（40% 不透明度 + 不可点击）

## 2. 手动测试

- [ ] 2.1 测试选择小说后的 tab 状态
  - 启动服务器：`start.bat`
  - 选择一本小说
  - 确认"进度" tab 显示"已选择小说"卡片
  - 确认"日志" tab 可用且不显示该卡片
  - 确认"调试" tab 可用且不显示该卡片
  - 确认"总结" tab 禁用（40% 不透明度 + 不可点击）
  - 确认其他分析 tab（雷点/角色/关系图/首次/统计/发展）禁用

- [ ] 2.2 测试分析完成后的 tab 状态
  - 点击"开始分析"按钮
  - 等待分析完成
  - 确认自动切换到"总结" tab
  - 确认所有 10 个 tab 均可用且正常切换
  - 确认"总结" tab 显示快速统计和关系总结内容

- [ ] 2.3 测试边界情况
  - 选择小说后，手动点击禁用的"总结" tab，确认无响应
  - 分析完成后，切换到"进度" tab，确认不再显示"已选择小说"卡片（因为 `hasAnyResult() === true`）

- [ ] 2.4 添加 E2E 自动化测试（新增测试文件）
  - 文件：`tests/test_tab_interaction_e2e.py`（新建）
  - 测试场景：
    - **场景 1：选择小说后，验证 tab 禁用状态**
      - 选择小说但不运行分析
      - 断言"进度" tab 可点击且为 active 状态
      - 断言"日志" tab 可点击（无 disabled 属性）
      - 断言"调试" tab 可点击（无 disabled 属性）
      - 断言"总结" tab 被禁用（有 disabled 属性 + opacity-40 样式）
      - 断言其他分析 tab（雷点/角色/关系图/首次/统计/发展）被禁用
    - **场景 2：选择小说后，验证"已选择小说"卡片只在"进度" tab 显示**
      - 选择小说但不运行分析
      - 在"进度" tab，断言卡片可见（包含小说名和字数）
      - 切换到"日志" tab，断言卡片不可见
      - 切换到"调试" tab，断言卡片不可见
      - 切换回"进度" tab，断言卡片再次可见
    - **场景 3：分析完成后，验证"总结" tab 可用且自动切换**
      - 选择小说并运行分析（使用 stub）
      - 断言分析完成后 currentTab 自动变为 "summary"
      - 断言"总结" tab 无 disabled 属性
      - 断言"总结" tab 内容正确渲染（#quickStats 可见）
    - **场景 4：分析完成后，验证"已选择小说"卡片不再显示**
      - 选择小说并运行分析
      - 切换到"进度" tab
      - 断言"已选择小说"卡片不可见（因为 hasAnyResult() === true）

## 3. 代码审查

- [ ] 3.1 检查是否有其他依赖 `alwaysEnabled` 属性的逻辑
  - 使用 Grep 搜索 `alwaysEnabled` 关键词
  - 确认只在 tab 启用/禁用判断中使用，无其他副作用

- [ ] 3.2 检查 CSS 样式是否正确应用
  - 确认 `opacity-40 cursor-not-allowed` 样式在 tab 禁用时生效
  - 确认 `disabled` 属性正确阻止点击事件

## 4. 自动化测试验证

- [ ] 4.1 运行新增的 E2E 测试
  - 命令：`python -m pytest tests/test_tab_interaction_e2e.py -v`
  - 确认所有 4 个场景通过

- [ ] 4.2 运行完整测试套件
  - 命令：`python -m pytest -q`
  - 确认无回归（现有测试不受影响）

## 5. 完成验证

- [ ] 5.1 确认所有手动测试点通过
- [ ] 5.2 确认所有自动化测试通过
- [ ] 5.3 运行 `openspec validate simplify-tab-interaction --strict` 确认规范一致性
- [ ] 5.4 更新 tasks.md 所有任务为 `[x]` 已完成状态
