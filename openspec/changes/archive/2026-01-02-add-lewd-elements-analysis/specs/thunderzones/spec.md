# thunderzones Delta Specification

## ADDED Requirements

### Requirement: 雷点类型覆盖（补全）
系统 SHALL 在雷点检测中覆盖以下雷点类型：
- 绿帽
- 强奸/迷奸
- NTR
- 恶堕
- 重口/血腥调教
- 其他

#### Scenario: 雷点输出仅使用允许类型集合
- **WHEN** 系统输出一条雷点记录
- **THEN** 其 `type` 字段属于上述允许集合之一（或在 UI 中可归一化到该集合）

### Requirement: 偏好型元素不作为雷点
系统 MUST 不把以下偏好型元素作为雷点输出：`乱伦`、`调教`（正常 SM/调教）、`恋足`、`萝莉`。

#### Scenario: 偏好型元素由“涩情元素”模块承载
- **WHEN** 文本包含乱伦/调教/恋足/萝莉
- **THEN** 系统通过“涩情元素”模块输出对应标签
- **AND** 雷点模块不得仅因这些元素存在而输出雷点

## MODIFIED Requirements

无（当前未存在 thunderzones capability spec；本 delta 作为新增规范化描述）

## REMOVED Requirements

无
