# Vue 前端代码结构设计（智能体协同模块）

## 1. 目标
当前前端设计只服务于“智能体协同模块”，不尝试把整个主系统前端一次性抽象完整。

核心要求：
- 能支撑三个工作台：画布、对话、监控
- 能独立开发后再并入更大的 Vue 主项目
- 结构清楚，但不过度拆分

## 2. 模块级推荐目录树
```text
agent-collab-module/
├─ src/
│  ├─ pages/
│  │  ├─ WorkflowCanvasPage.vue
│  │  ├─ ChatWorkbenchPage.vue
│  │  └─ MonitorWorkbenchPage.vue
│  ├─ components/
│  │  ├─ canvas/
│  │  │  ├─ WorkflowCanvas.vue
│  │  │  ├─ NodePalette.vue
│  │  │  ├─ NodeConfigPanel.vue
│  │  │  └─ nodes/
│  │  ├─ chat/
│  │  │  ├─ ChatSidebar.vue
│  │  │  ├─ ChatWindow.vue
│  │  │  ├─ ApprovalCard.vue
│  │  │  └─ MessageComposer.vue
│  │  ├─ monitor/
│  │  │  ├─ MetricsCards.vue
│  │  │  ├─ ExecutionTable.vue
│  │  │  ├─ DeadletterTable.vue
│  │  │  └─ AlertPanel.vue
│  │  └─ shared/
│  │     ├─ AgentStatusTag.vue
│  │     ├─ ExecutionStatusTag.vue
│  │     ├─ VTableWrapper.vue
│  │     └─ DynamicFormRenderer.vue
│  ├─ api/
│  │  ├─ workflows.ts
│  │  ├─ executions.ts
│  │  ├─ chat.ts
│  │  └─ monitor.ts
│  ├─ store/
│  │  ├─ workflow.ts
│  │  ├─ chat.ts
│  │  └─ monitor.ts
│  ├─ composables/
│  │  ├─ useWorkflowCanvas.ts
│  │  ├─ useWorkflowPublish.ts
│  │  ├─ useChatSession.ts
│  │  ├─ useApprovals.ts
│  │  └─ useExecutionStream.ts
│  ├─ types/
│  │  ├─ workflow.ts
│  │  ├─ execution.ts
│  │  ├─ chat.ts
│  │  └─ monitor.ts
│  ├─ router/
│  │  └─ agentCollab.ts
│  ├─ styles/
│  │  └─ index.css
│  └─ utils/
│     ├─ canvasMapper.ts
│     ├─ dslCompiler.ts
│     └─ permission.ts
└─ index.ts
```

## 3. 这样设计的原因

### 3.1 只保留模块内最必要的层次
- `pages/`：三个工作台页面
- `components/`：按画布 / 对话 / 监控分类
- `api/`：和 Python 服务对接
- `store/`：模块内状态
- `composables/`：页面交互逻辑
- `types/`：和后端契约对齐

这已经足够支撑协同模块开发，不需要提前拆成过多 feature 子包。

### 3.2 兼容未来合并
- 将来并入主 Vue 项目时，可以把整个 `agent-collab-module/src` 作为一个业务模块接入
- 只需要把 `router/agentCollab.ts` 挂进主路由
- 页面和组件不会散落到主项目各处，方便整体迁移

### 3.3 shared 只放模块内共享
这里的 `components/shared/` 只服务于智能体协同模块内部复用，
不是全系统级 shared，避免后续与主项目公共组件冲突。

## 4. 三个工作台各自负责什么

### 4.1 WorkflowCanvasPage.vue
负责：
- 工作流画布编辑
- 节点拖拽与连线
- 节点配置
- 草稿保存 / 编译 / 发布
- 版本查看

感知型节点第一阶段必须优先支持：
- 数据库实时感知配置
- 数据源系统选择
- 表 / 字段选择
- 条件构建器
- 输出事件映射配置

控制节点当前阶段建议补充：
- `ConditionNode.vue`
- `ParallelNode.vue`
- `LoopNode.vue`
- `SubflowNode.vue`
- `WaitNode.vue`
- `ApprovalNode.vue`
- `ExceptionNode.vue`

对应配置面板建议支持：
- 分支条件配置
- 并行分支配置
- 循环条件 / 最大次数
- 子流程引用选择
- 等待条件配置
- 审批模板配置
- 异常兜底配置

### 4.2 ChatWorkbenchPage.vue
负责：
- 会话列表
- 对话消息展示
- 命令输入
- 审批卡片展示
- 执行结果回传

当前阶段必须新增：
- 独立审批工作区
- 审批意见输入
- 执行结果卡片 / 执行失败卡片
- 部门切换后的 workflow 查询与触发入口
- 语音 / PDF / 图片上传入口

对话工作台当前阶段建议拆分：
- `DepartmentWorkflowCatalog.vue`：按部门 + 职能分类查询 workflow
- `ApprovalWorkbench.vue`：审批任务区
- `ExecutionResultCard.vue`：执行结果展示
- `AttachmentPanel.vue`：语音 / PDF / 图片上传入口

### 4.3 MonitorWorkbenchPage.vue
负责：
- 执行状态概览
- 异常任务与死信查看
- 核心指标展示
- 告警信息展示

当前阶段必须新增：
- incident 列表
- timeout / consistency / compliance / health 分类筛选
- 干预动作入口（暂停 / 重试 / 标记人工复核 / 隔离）
- 操作人历史与处理记录展示

## 5. 与后端契约的直接映射
- `api/workflows.ts` 对接 workflow 草稿/编译/发布/版本接口
- `api/executions.ts` 对接执行启动/状态/恢复/时间线接口
- `api/chat.ts` 对接对话会话、消息、审批接口
- `api/monitor.ts` 对接监控指标、执行列表、死信接口

监控工作台前端建议补充：
- `components/monitor/IncidentTable.vue`
- `components/monitor/IncidentDetailDrawer.vue`
- `components/monitor/RecoveryActionPanel.vue`
- `types/monitor.ts` 中的 `IncidentItem`

对话型节点前端建议补充：
- `components/chat/DepartmentWorkflowCatalog.vue`
- `components/chat/ApprovalWorkbench.vue`
- `components/chat/ExecutionResultCard.vue`
- `components/chat/AttachmentPanel.vue`
- `types/chat.ts` 中的 `ChatRouteType`、`WorkflowCatalogItem`

感知型节点前端建议补充：
- `components/canvas/nodes/SensorNode.vue`
- `components/canvas/panels/SensorConfigPanel.vue`
- `types/workflow.ts` 中的 `SensorNodeConfig`
- `utils/dslCompiler.ts` 中的 sensor 节点编译规则

决策型节点前端建议补充：
- `components/canvas/nodes/DecisionNode.vue`
- `components/canvas/panels/DecisionConfigPanel.vue`
- `types/workflow.ts` 中的 `DecisionNodeConfig`
- `utils/dslCompiler.ts` 中的 decision 节点编译规则

决策型节点第一阶段必须优先支持：
- 三种模式单选：规则型 / 模型型 / 智能型
- 根据模式动态切换配置区内容
- 统一输出配置区

执行型节点前端建议补充：
- `components/canvas/nodes/ExecutionNode.vue`
- `components/canvas/panels/ExecutionConfigPanel.vue`
- `components/chat/ApprovalWorkbench.vue`
- `components/chat/ExecutionResultCard.vue`
- `types/workflow.ts` 中的 `ExecutionNodeConfig`

执行型节点第一阶段必须优先支持：
- 执行目标模式选择：手动 / AI 判断
- 是否进入对话审批开关
- 审批卡片投递到对话工作区
- 执行结果回传到对话工作区

## 6. 前后端并行开发建议
- 前端先根据 `types/*.ts` 固定页面数据结构
- 画布页优先联调 `workflow-dsl.md` 对应的 `ui_schema`
- 对话页优先联调 `python-service-api.md` 与 `api-event-contracts.md`
- 监控页优先联调 `Monitor API` 和 SSE 事件

对话页还应优先联调：
- workflow 注册目录查询接口
- 审批工作区接口
- 多模态上传与消息归一化接口

## 7. 合并进主 Vue 项目时的规则
- 保持 `agentCollab.ts` 为单独路由模块
- 页面入口保持在 `pages/`
- 不在模块内写死主系统菜单、主布局、全局权限实现
- 需要对接主系统时，只适配：路由注册、鉴权注入、HTTP client 注入
