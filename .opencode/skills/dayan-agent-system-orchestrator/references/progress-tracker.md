# 开发进度跟踪模板

> 使用规则：每次执行方案后必须更新本文件，至少同步“已完成模块 / 进行中模块 / 下一步 / 文档同步状态”。

## 当前里程碑
- M2 画布与工作流编排

## 当前阶段目标
- 细化五类智能体与控制节点设计，优先收敛主链与控制节点定义边界

## 已完成模块
- Python 服务基础骨架
- 前端智能体协同模块基础骨架
- 感知型智能体高层架构定义
- 决策型智能体高层架构定义
- 执行型智能体高层架构定义
- 对话型智能体高层架构定义
- 监控型智能体高层架构定义
- 控制节点高层架构定义
- skill 文档全量审查与主要冲突修正
- 前后端代码骨架与最新 skill 文档口径对齐

## 进行中模块
- 感知型智能体详细设计（数据库实时感知优先）
- 决策型智能体详细设计（三种决策模式）
- 执行型智能体详细设计（对话审批与结果回传优先）
- 对话型智能体详细设计（部门化路由与 workflow 目录优先）
- 监控型智能体详细设计（独立监控工作台、非画布节点）
- 控制节点详细设计（定义先行，开发后置）

## 未开始模块
- 感知型智能体 Go 事件接入实现
- 感知型节点前端真实配置表单实现
- 感知型智能体 handler 与订阅匹配实现
- 决策型节点真实配置表单实现
- 决策型智能体 rule/model/llm 三模式 handler 实现
- 执行型节点真实配置表单实现
- 执行型审批工作区与执行结果卡片实现
- 执行型智能体目标注册表与 handler 实现
- 对话型 workflow 目录查询界面实现
- 对话型智能体 ask/approve/command 路由实现
- 多模态消息归一化实现
- monitor incident 模型实现
- monitor workbench 真实页面实现
- 监控干预动作 API 实现
- 控制节点配置面板实现
- 控制节点运行时主链实现

## 阻塞项
- Go 侧事件 envelope 最终字段与投递格式尚未完全联调

## 风险项
- 感知型节点前端配置过复杂，可能影响 M2 交付节奏
- 数据库实时感知与未来 IoT/Webhook 扩展需要统一抽象，避免后期重构
- 决策型三模式配置差异较大，需要避免前端面板过于复杂
- 执行型“手动目标 / AI 选择目标”与审批逻辑耦合，需避免前端面板过重
- 对话型 workflow 路由若过度依赖自然语言匹配，容易误选 workflow
- 部门权限与用户个人记录若不拆开，容易出现同权不同记录混乱
- 监控型智能体若过度干预 execution，将演变成隐藏执行引擎
- 控制节点若定义不统一，后续 execution_dag 与前端配置可能分裂
- 前端构建已通过，但当前打包体积较大，后续需做代码分割优化

## 下一步
- 将控制节点的 DSL 字段、前端配置项与优先实现顺序继续细化到可开发级

## 文档同步状态
- project-overview.md：无需更新
- architecture.md：已同步五类智能体与控制节点的最新边界
- workflow-dsl.md：已同步 monitor 非节点化与控制节点最小配置
- database-design.md：已同步 workflow_registry / incidents / execution target 等核心结构
- api-event-contracts.md：已同步 chat route / workflow catalog / monitor incidents 等关键契约
- implementation-plan.md：已同步当前系统设计后的阶段任务口径
- change-log.md：已同步感知/决策/执行/对话/监控/控制节点设计变更

## 文档同步状态
- project-overview.md：无需更新
- architecture.md：已同步对话型、监控型与控制节点边界
- workflow-dsl.md：已同步控制节点最小配置，并确认 monitor 不属于普通画布节点
- database-design.md：已同步 workflow_registry、chat 留痕约束、incidents 等设计
- api-event-contracts.md：已同步 chat / monitor 既有契约
- implementation-plan.md：已同步对话型、监控型、控制节点优先任务，并修正 M4 编号冲突
- change-log.md：已同步对话型、监控型、控制节点设计变更
