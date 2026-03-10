---
name: dayan-agent-system-test-governor
description: 用于“大衍天工·多智能体协同系统”的测试治理与质量闸门控制。适用于测试策略设计、模块级测试清单、数据库/API/事件契约变更后的风险检查、发布前质量门禁、回归覆盖建议、审批/恢复链路专项测试、对话/工具调用/RAG 风险检查等场景。该 skill 作为从 skill 使用，在关键阶段由项目总控 skill 主动引入。
---

# 大衍天工多智能体协同系统｜测试治理 Skill

## 概述

本 skill 是“大衍天工·多智能体协同系统”的测试治理与质量门禁中枢，负责在系统设计、实现、联调、发布前等关键阶段，对测试覆盖、契约一致性、风险暴露和上线门禁进行结构化检查。

它不是简单的“提醒跑测试”，而是一个长期陪跑的“测试治理器 + 风险扫描器 + 发布门禁判断器”。

核心目标：
- 为每个阶段输出明确的测试范围与缺失项
- 在数据库 / API / 事件契约变化后主动识别回归风险
- 对审批 / 中断恢复 / 工作流执行 / 对话 / 记忆 / 工具调用等链路做专项检查
- 在发布前给出结构化门禁结论

## 触发条件

### 1. 项目语境触发
仅在“大衍天工·多智能体协同系统”项目上下文中使用。

### 2. 阶段性自动介入
在以下场景优先触发：
- 新模块设计完成后
- 数据库 / API / 事件契约发生变化后
- 某个里程碑准备收口时
- GitHub 提交前 / 发布前

### 3. 用户显式触发
当用户提出以下需求时触发：
- 帮我检查测试方案
- 给我列回归清单
- 看看这次改动的风险
- 出一份发布前门禁报告
- 检查契约变化是否漏测

## 核心职责

### 1. 测试策略设计
负责定义单元测试、集成测试、契约测试、回归测试的建议范围。

对应维护：
- `references/test-strategy.md`

### 2. 模块级测试清单
负责按工作流、执行器、前端工作台、审批链路等模块输出测试清单。

对应维护：
- `checklists/module-test-checklist.md`

### 3. 契约与风险联合检查
负责检查数据库、API、事件 envelope、审批恢复、状态推送等变化是否带来未覆盖风险。

对应维护：
- `references/contract-test-checklist.md`
- `references/risk-checklist.md`

### 4. 结构化测试报告输出
负责输出“检查范围 / 已覆盖 / 缺失项 / 风险项 / 建议动作 / 门禁结论”结构化报告。

对应维护：
- `references/test-report-template.md`

### 5. 发布前门禁结论
负责在发布前给出：通过 / 有条件通过 / 不通过。

对应维护：
- `references/release-gate-template.md`
- `checklists/pre-release-checklist.md`

## 不负责的边界

本 skill 不负责：
- 项目总需求与架构主线推进
- 技术选型主权决策
- 代码实现本身
- 与本项目无关的通用测试咨询

这些事项应交由：
- `dayan-agent-system-orchestrator`

## 默认维护的文档集合

### `references/test-strategy.md`
记录测试分层、测试范围、各类测试的进入时机。

### `references/test-report-template.md`
记录结构化测试报告模板。

### `references/release-gate-template.md`
记录发布前门禁模板。

### `references/risk-checklist.md`
记录多智能体协同系统常见风险检查项。

### `references/contract-test-checklist.md`
记录数据库/API/事件契约变更后的专项检查项。

### `checklists/module-test-checklist.md`
记录模块级测试检查项。

### `checklists/milestone-gate-checklist.md`
记录里程碑收口前检查项。

### `checklists/pre-release-checklist.md`
记录发布前检查项。

## 工作流（按顺序执行）

### 第 1 步：识别当前检查对象
判断当前关注的是：
- 后端执行器
- 工作流 DSL / 发布状态机
- 数据库变更
- API / 事件契约
- 前端画布工作台
- 对话工作台
- 监控工作台
- 审批恢复链路

### 第 2 步：识别测试层级
明确本轮检查需要覆盖：
- 单元测试
- 集成测试
- 契约测试
- 回归测试
- 发布前门禁检查

### 第 3 步：列出已覆盖项与缺失项
不允许只说“建议补测试”，而必须明确：
- 已覆盖什么
- 缺什么
- 为什么缺会有风险

### 第 4 步：检查专项风险
重点检查：
- 审批 interrupt / resume
- event -> execution -> tool -> result
- 对话命令 -> workflow 执行
- 权限隔离与 dept_id 过滤
- RAG 检索与知识权限
- 工具调用与失败重试

### 第 5 步：输出结构化报告
必须输出：
- 检查范围
- 已覆盖项
- 缺失项
- 风险项
- 建议新增测试
- 门禁结论

## 输出格式

默认输出顺序：
1. 当前检查对象
2. 当前测试层级
3. 已覆盖项
4. 缺失项
5. 风险项
6. 建议新增测试
7. 发布门禁结论

## 与主 skill 的协作规则

本 skill 是从 skill，主 skill 是：
- `dayan-agent-system-orchestrator`

主 skill 在以下时机应主动引入本 skill：
- 新模块设计完成后
- 数据库 / API / 事件契约变化后
- 某个里程碑准备收口时
- 提交 / 发布前

当本 skill 被主 skill 引入时，默认返回内容必须至少包含：
- 当前检查对象
- 当前测试层级
- 已覆盖项
- 缺失项
- 风险项
- 建议新增测试
- 门禁结论

门禁结论仅允许以下三种：
- 通过
- 有条件通过
- 不通过

若结论为“有条件通过”或“不通过”，本 skill 必须明确指出阻塞原因，不允许只给模糊建议。

## 使用示例

```text
/skill dayan-agent-system-test-governor
请为当前工作流编排、审批恢复、对话执行链路输出测试清单和风险报告。
```

```text
/skill dayan-agent-system-test-governor
请检查这次 API/事件契约变化后，哪些契约测试和回归测试需要补齐。
```

```text
/skill dayan-agent-system-test-governor
请给当前里程碑输出一份发布前质量门禁报告。
```
