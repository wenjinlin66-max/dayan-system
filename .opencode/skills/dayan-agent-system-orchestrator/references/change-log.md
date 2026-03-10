# 变更记录模板

| 日期 | 变更主题 | 变更原因 | 影响范围 | 已同步文档 | 备注 |
|---|---|---|---|---|---|
| 2026-03-10 | 感知型智能体优先落数据库实时感知 | 用户要求先细化感知型智能体，初期仅实现数据库感知并为后续扩展预留 | 架构、DSL、数据库、前端节点配置、实施计划、进度、事件契约 | architecture.md; workflow-dsl.md; database-design.md; frontend-code-structure.md; implementation-plan.md; progress-tracker.md; api-event-contracts.md | Go 发布数据库业务变更事件，Python 做订阅匹配与标准化 |
| 2026-03-10 | 决策型智能体细化为三种模式配置 | 用户要求决策型节点支持规则型、模型型、智能型三种模式，并根据模式显示不同设置面板 | 架构、DSL、数据库、前端节点配置、实施计划、进度 | architecture.md; workflow-dsl.md; database-design.md; frontend-code-structure.md; implementation-plan.md; progress-tracker.md | 前端采用“模式选择 + 模式专属配置 + 统一输出配置” |
| 2026-03-10 | 决策型智能体统一输出结构定案 | 为避免下游执行型、审批型、对话型适配三套返回格式，统一决策输出契约 | 架构、DSL、事件契约、进度 | architecture.md; workflow-dsl.md; api-event-contracts.md; progress-tracker.md | 三种模式统一输出 decision_summary / decision_payload / risk_level / recommended_actions / explanation / citations |
| 2026-03-10 | 执行型智能体优先落对话审批与结果回传主链 | 用户要求执行型先实现对话审批工作区与执行结果回传，第三方目标后续扩展 | 架构、DSL、数据库、前端节点配置、事件契约、实施计划、进度 | architecture.md; workflow-dsl.md; database-design.md; frontend-code-structure.md; api-event-contracts.md; implementation-plan.md; progress-tracker.md | 第一阶段支持手动目标 / AI 选择目标，并配置是否进入对话审批 |
| 2026-03-10 | 对话型智能体定为部门化主入口与 workflow 路由器 | 用户要求对话型智能体承担部门问答、审批、工作流触发、多模态入口与 workflow 目录发现 | 架构、DSL、数据库、前端、API、实施计划、进度 | architecture.md; workflow-dsl.md; database-design.md; frontend-code-structure.md; api-event-contracts.md; python-service-api.md; implementation-plan.md; progress-tracker.md | 不能只靠自然语言直接硬选 workflow，必须先经过 workflow registry + 部门/角色过滤 + 歧义确认 |
| 2026-03-10 | 监控型智能体定为独立控制平面子系统 | 用户要求监控型智能体单独做监控界面，不作为画布节点，先定义细节后最后开发 | 架构、DSL、数据库、前端、API、实施计划、进度 | architecture.md; workflow-dsl.md; database-design.md; frontend-code-structure.md; api-event-contracts.md; implementation-plan.md; progress-tracker.md | 监控型智能体负责超时、一致性、异常、合规、健康五类规则，并通过 incident 模型与受控动作 API 工作 |
| 2026-03-10 | 控制节点定义先行 | 用户要求先定义条件分支、并行、循环、子流程、等待、审批、异常兜底等控制节点，具体开发可后置 | 架构、DSL、前端、实施计划、进度 | architecture.md; workflow-dsl.md; frontend-code-structure.md; implementation-plan.md; progress-tracker.md | 控制节点只负责决定下一步流向，不直接调用模型或操作业务数据库 |
