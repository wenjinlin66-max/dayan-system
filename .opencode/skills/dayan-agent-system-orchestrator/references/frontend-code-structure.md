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

### 4.2 ChatWorkbenchPage.vue
负责：
- 会话列表
- 对话消息展示
- 命令输入
- 审批卡片展示
- 执行结果回传

### 4.3 MonitorWorkbenchPage.vue
负责：
- 执行状态概览
- 异常任务与死信查看
- 核心指标展示
- 告警信息展示

## 5. 与后端契约的直接映射
- `api/workflows.ts` 对接 workflow 草稿/编译/发布/版本接口
- `api/executions.ts` 对接执行启动/状态/恢复/时间线接口
- `api/chat.ts` 对接对话会话、消息、审批接口
- `api/monitor.ts` 对接监控指标、执行列表、死信接口

## 6. 前后端并行开发建议
- 前端先根据 `types/*.ts` 固定页面数据结构
- 画布页优先联调 `workflow-dsl.md` 对应的 `ui_schema`
- 对话页优先联调 `python-service-api.md` 与 `api-event-contracts.md`
- 监控页优先联调 `Monitor API` 和 SSE 事件

## 7. 合并进主 Vue 项目时的规则
- 保持 `agentCollab.ts` 为单独路由模块
- 页面入口保持在 `pages/`
- 不在模块内写死主系统菜单、主布局、全局权限实现
- 需要对接主系统时，只适配：路由注册、鉴权注入、HTTP client 注入
