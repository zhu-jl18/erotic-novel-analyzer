# lewd-elements Delta Specification

## ADDED Requirements

### Requirement: 独立“涩情元素”分析能力
系统 SHALL 提供一个独立于“雷点(thunderzones)”的分析能力，用于输出特定色情元素标签（不算雷点）。

#### Scenario: 并行执行涩情元素分析
- **WHEN** 用户运行一次完整分析流程
- **THEN** 系统对同一份小说内容执行涩情元素分析
- **AND** 该分析与现有 `scenes`/`thunderzones` 并行执行（不互相阻塞）

### Requirement: 涩情元素类型集合
系统 SHALL 仅输出以下 4 类涩情元素：`乱伦`、`调教`、`恋足`、`萝莉`。

#### Scenario: 输出仅包含允许类型
- **WHEN** 系统输出涩情元素列表
- **THEN** 每条元素的 `type` 必须属于 {乱伦, 调教, 恋足, 萝莉}

### Requirement: 每类最多一条示例
系统 SHALL 对每个涩情元素类型最多输出一条示例；若该类型不存在则不输出该类型。

#### Scenario: 类型存在时输出单条示例
- **WHEN** 小说内容包含某类涩情元素
- **THEN** 输出 `type` 为该类别的一条记录
- **AND** 记录包含非空 `example`

#### Scenario: 同一类型不重复
- **WHEN** 小说内容包含多处同类涩情元素
- **THEN** 系统仍只输出该类型的一条代表性示例（不重复列出）

### Requirement: “萝莉”严格口径
系统 MUST 仅在文本存在明确未成年/低龄证据时才输出 `type=萝莉`。

#### Scenario: 明确未成年证据时标注萝莉
- **WHEN** 文本明确包含未成年/低龄信息（例如 <18、未成年、小学生/初中生等）
- **THEN** 系统可以输出 `type=萝莉` 并提供一个代表性 `example`

#### Scenario: 仅幼态描述不得标注萝莉
- **WHEN** 文本仅出现“幼态/娇小/萝莉风”等描述但没有明确未成年证据
- **THEN** 系统不得输出 `type=萝莉`

### Requirement: UI Tab 展示
前端 SHALL 提供一个名为“涩情元素”的 Tab，用于展示涩情元素总结与列表。

#### Scenario: 分析完成后 Tab 可用
- **WHEN** 分析完成
- **THEN** “涩情元素” Tab 可用且可切换
- **AND** Tab 内容展示：总结 + 4 类元素（仅显示存在项）

## MODIFIED Requirements

无（新增 capability）

## REMOVED Requirements

无
