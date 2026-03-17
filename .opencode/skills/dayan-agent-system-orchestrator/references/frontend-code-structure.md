# Vue 前端代码结构设计（智能体协同模块）

## 1. 目标
当前前端设计只服务于“智能体协同模块”，不尝试把整个主系统前端一次性抽象完整。

核心要求：
- 能支撑四个长期/临时工作台：画布、对话、监控，以及临时业务表格测试工作台
- 能支撑一个工作流查看区：统一查询所有 workflow
- 能独立开发后再并入更大的 Vue 主项目
- 结构清楚，但不过度拆分
- 顶部导航顺序当前收口为：工作流制作区 → 工作流查看区 → 对话区 → 监控区 → 业务表格区（临时）
- 工作流分类交互当前已开始落地为“部门 → 触发逻辑”两层浏览，查看区优先按部门，再按触发逻辑分类展示 workflow

## 2. 模块级推荐目录树
```text
agent-collab-module/
├─ src/
│  ├─ pages/
│  │  ├─ WorkflowCanvasPage.vue
│  │  ├─ ChatWorkbenchPage.vue
│  │  ├─ MonitorWorkbenchPage.vue
│  │  ├─ WorkflowLibraryPage.vue
│  │  └─ RecordsWorkbenchPage.vue
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
│  │  ├─ layout/
│  │  │  └─ WorkspaceTopNav.vue
│  │  └─ shared/
│  │     ├─ AgentStatusTag.vue
│  │     ├─ ExecutionStatusTag.vue
│  │     ├─ VTableWrapper.vue
│  │     └─ DynamicFormRenderer.vue
│  ├─ api/
│  │  ├─ workflows.ts
│  │  ├─ executions.ts
│  │  ├─ chat.ts
│  │  ├─ monitor.ts
│  │  └─ records.ts
│  ├─ store/
│  │  ├─ workflow.ts
│  │  ├─ chat.ts
│  │  ├─ monitor.ts
│  │  └─ records.ts
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
│  │  ├─ monitor.ts
│  │  └─ records.ts
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
- `pages/`：工作流制作区、对话区、监控区、工作流查看区、业务表格区
- `components/`：按画布 / 对话 / 监控 / records 分类
- `api/`：和 Python 服务对接

工作流制作区顶部信息栏口径：
- 保留字段内容不变，但应持续压缩顶部占高
- 标题区、状态胶囊、字段输入区、动作区优先采用更紧凑的垂直节奏与圆角包裹
- 目标是让更多首屏空间留给画布本体，而不是让元信息区占据过高高度
- `加载已有流程` 的宽度不应因布局压缩而明显小于其余字段，需与同排其他输入位保持接近的视觉体量
- 制作区应提供 workflow 删除按钮；当前口径为删除对应 workflow 定义数据（workflow / versions / registry），并从前端暴露面中消失
- 当画布内存在 `sensor_agent` 节点时，制作区顶部动作栏应提供一个紧凑型“模拟感知事件”入口，直接调用 Python Mock Event Injector 验证当前感知链路，不额外开辟独立页面
- `store/`：模块内状态
- `composables/`：页面交互逻辑
- `types/`：和后端契约对齐

### 3.2 顶部导航当前口径
- 顶部导航使用共享组件统一呈现工作区切换，不再由各页面各自发明入口
- 当前导航项至少包含：`工作流制作区 / 对话区 / 监控区 / 工作流查看区 / 业务表格区`
- 导航的目标是把“系统有哪几个工作区”明确暴露出来，而不是把入口埋在某个页面内部卡片中

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

当前已定下的交互口径：
- 页面顶部采用紧凑型 workflow studio 工具条，不允许放置无实际功能支撑的装饰性按钮
- 工作流名称、编码、workflow_id、编译状态、发布版本应以紧凑信息卡形式展示，避免顶部信息区过度占屏
- workflow 首屏优先保证画布成为主视觉区域；基础信息、编译预览、版本历史应优先采用 tabs / 折叠式布局，而不是在首屏并排占用大面积固定卡片
- 节点来源不再长期占用左侧固定面板，而是由画布内 `+` 按钮触发“节点面板”浮层
- 节点面板应在画布内部弹出，按“智能体节点 / 流程控制”分组供选择
- 点击节点后打开节点配置弹窗，而不是长期固定右侧设置栏
- 画布左下角应保留放大、缩小、居中（fit view）三个基础控制按钮
- 允许在辅助区保留结构摘要、快捷连线、删除节点/删除连线等编辑器工具，但不应喧宾夺主
- compile error 与“需重新编译后才能发布”的提示必须贴近发布操作区，而不是藏在其他页面区域
- workflow 名称与编码输入必须实时同步到 store / 当前编辑态，不得依赖失焦后才回写
- save / compile / publish / load 等异步动作必须具备 pending 锁，避免响应乱序覆盖当前 workflow 状态
- workflow 加载时必须将“当前可编辑状态”与“上次加载/上次编译快照”分离，避免共享引用导致快照被污染
- 工作流查看区中的 `前往制作区` 不应只跳到空白画布；必须携带 `workflowId` 并在 `WorkflowCanvasPage.vue` 中自动加载该 workflow 的最新 draft `ui_schema`，若 draft 缺失则回退加载 current release 的 `ui_schema`，保证已保存/已发布 workflow 进入制作区后都能看到真实节点与连线
- workflow 制作区当前应提供“所属部门”选择，允许配置员在创建阶段显式决定该 workflow 归属哪个 ERP 部门；加载已有流程列表默认跟随当前所选部门过滤
- workflow 制作区顶部动作栏当前应提供显式的 `新建工作流` 按钮，用于退出当前已加载流程并开启一个新的未保存 workflow；若当前画布有未保存修改，必须先给出覆盖确认
- workflow 运行时，当前执行节点应在画布中出现明显的动态炫彩高亮，且高亮位置应跟随后端 `current_node` 变化实时移动
- 为保证节点高亮真的可见，制作区的 mock event inject 当前应采用“先返回 execution_id、后端后台继续执行、前端轮询 execution 状态”的方式，而不是等整条 workflow 同步跑完再返回
- 工作流执行历史弹窗当前必须补“执行结果”摘要区，不再只展示任务/对象/时间三块粗信息；对于执行型历史项，应直接展示执行是否成功、写入到哪个对象，以及字段级变更明细
- `ExecutionConfigPanel.vue` 当前已从“只配置 department_table 写入”扩展为“多目标 / chat-delivery”面板：当 `结果回传=对话区` 且目标编码留空时，执行型节点进入 chat-only 模式，只把决策结果整理为 AI 风险报告发到目标部门对话框，不做业务表写入
- 执行型面板当前应支持：`result_target_dept_id`、`chat_delivery.send_summary/send_failure_reason`、`result_template` 三类对话回传配置；模板变量至少包含 `decision_summary / risk_level / decision_explanation / recommended_actions / target_item_id / recommended_quantity / result_summary`
- `ExecutionConfigPanel.vue` 当前已进一步收口为“单目标执行器”面板：配置员必须先明确当前 execution 节点的主目标类型（`department_chat / department_table / feishu / email / mcp`），再填写该目标的路由与参数
- 若同一条 workflow 既要“发部门对话框风险报告”又要“修改业务表格/调第三方工具”，前端应引导配置员在 `decision_agent` 后插入 `parallel` 节点，并并列创建多个 `execution_agent`；不要继续把多个业务目标混在一个 execution 节点的面板里
- `department_chat` 目标当前应直接作为执行目标类型出现，而不是藏在“结果回传”概念下；表格执行结果的摘要通知仍可保留 `result_delivery` 作为辅助配置，但不应替代独立 chat 执行节点
- 业务表格区当前是临时测试入口，但应能触发配置为 `erp_prod` 的库存/工单/设备类感知 workflow；后端已为 `dayan_mock_records <-> erp_prod` 增加兼容匹配，避免配置员在表格区改了数据却发现 execution 仍为空
- 对话区当前已进入“部门身份 + CEO 总览”第一版：前端通过身份面板切换账号与范围，部门账号只看自己的部门会话；CEO 账号可切到全部门总览，并按部门过滤会话、流程目录与审批待办
- `ChatSidebar.vue`、`DepartmentWorkflowCatalog.vue`、`ApprovalWorkbench.vue`、`MessageComposer.vue` 当前都必须感知 chat identity scope；CEO 在“全部门”模式下默认以跨部门查看为主，切到具体会话后再继续阅读/操作
- 当前已开始落地真正账号登录模型：新增 `LoginPage.vue`、auth store、路由守卫和 `/login` 入口；未登录用户默认不能进入工作台，必须先登录生产部/仓储部/供应链部/CEO 账号
- `ChatIdentityPanel.vue` 当前已从“伪登录身份切换器”收敛为“当前登录账号 + CEO 范围控制器”；普通部门账号只显示当前身份，CEO 账号才允许切换单部门/全部门视图与聚焦部门
- `ChatWindow.vue` 当前在 CEO 全部门模式下会显示消息所属部门标签；`ApprovalWorkbench.vue` 与 `ExecutionResultCard.vue` 也已补部门过滤入口，用于跨部门审批和执行结果筛选
- `ChatWindow.vue` 当前消息头应显示时间：历史消息优先使用后端返回的 `created_at`，本地刚发送的用户消息也应立即带本地时间，避免“发送后短暂无时间、刷新后才出现”的割裂体验
- CEO 单部门模式当前不再退化为“普通用户只看自己 user_id 的会话”；前端会统一以 `include_all=true + dept_id=<目标部门>` 方式请求 chat / approvals / executions 范围接口，保证 CEO 在聚焦生产部时能直接看到生产部真实会话与结果，而不是空白或 404
- CEO 在具体部门会话中的“发送消息 / 从 chat 启动 workflow”当前也必须复用同一套 `include_all=true + dept_id=<目标部门>` scope 参数，不能只在列表/消息读取时带 scope、而在写操作上退回 `ceo` 本部门作用域
- CEO 右侧 workflow 目录当前已按 `workflow_id` 去重，不再因为 `workflow_registry` 多版本有效记录而把同一个 workflow 重复渲染成多张卡片

感知型节点第一阶段必须优先支持：
- 数据库实时感知配置
- 数据源系统选择
- 表 / 字段选择
- 条件构建器
- 输出事件映射配置
- 输出映射中的 `payload.*` 默认指向数据库变更事件的 `after` 快照，`event.*` 指向原始事件信封，降低配置员对事件嵌套结构的理解成本
- 来源系统 / 表 / 事件键 / 条件字段 / 操作符 应优先通过后端 `sensor-metadata` 目录接口联动选择，不再默认使用自由输入框

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

当前阶段节点配置交互规则：
- 新增节点后应直接进入该节点的配置态
- 节点配置弹窗需按节点类型展示不同表单字段
- JSON 高级配置允许保留，但应位于类型化表单之后，作为高级配置区

### 4.2 ChatWorkbenchPage.vue
负责：
- 会话列表
- 对话消息展示
- 命令输入
- 审批卡片展示
- 执行结果回传

当前已定下的交互口径：
- `DepartmentWorkflowCatalog.vue` 中的 workflow 项可直接点击启动，不仅用于只读展示
- 对话消息中若存在多个候选 workflow，应在消息卡片中渲染“直接启动该候选”的按钮
- workflow 目录启动与候选确认启动必须复用同一条前端启动逻辑，避免出现两套状态处理
- 当 workflow 存在 `required_inputs` 时，目录卡片与消息卡片都必须能切入“参数补齐卡片”，而不是分裂出另一套临时启动表单
- execution 结果卡片需支持实时状态更新；当前策略为 SSE 优先、轮询兜底
- 前端应暴露最小状态反馈：当前 execution 状态、当前节点、是否处于实时流连接/轮询兜底状态
- 会话侧栏应强调“当前部门对话框”概念，优先展示部门会话，而不是暗示用户按 workflow 建会话
- `DepartmentWorkflowCatalog.vue` 应按 `workflow_category` 分组展示当前部门可用 workflow，而不是平铺 workflow 列表
- 审批提醒、审批结果、执行结果应能回流到 `ChatWindow.vue` 的消息流中，侧边审批区保留为操作面而不是唯一展示面
- `ChatWorkbenchPage.vue` 中间主区域应以 `ChatWindow + MessageComposer` 组成完整 AI 对话主窗口，ExecutionResult / Attachment / Approval / WorkflowCatalog 让位到侧边辅助区
- `MessageComposer.vue` 默认按“问答优先、流程辅助”设计，不再只以命令输入形态出现
- 中间主对话区应避免重复出现“AI 主区域说明卡”，保留消息流与输入框本体即可，减少装饰性文案占位
- 多模态输入的最终目标形态应并入主输入框交互（像通用大模型产品一样由用户直接拖入图片/PDF或切换输入模式），当前阶段不再在页面上单独展示附件入口卡片
- 左侧辅助区应优先放置“最近历史会话 + 审批待办 + 执行结果”，右侧收口为流程目录，避免把审批信息放到离会话太远的位置
- `ChatSidebar.vue` 默认只展示少量最近会话，完整历史应通过居中弹窗打开供用户选择，而不是长列表直接占满侧栏
- 对话区中的部门 workflow 目录当前应为每条 workflow 提供“执行历史”入口，点击后在中间弹窗中查看该 workflow 在当前部门下的执行记录，并按执行类型分类展示

工作流查看区分类/删除口径：
- 查看区当前筛选项应显示为“触发逻辑分类”，不再使用助手自行定义的业务分类
- workflow 卡片需提供删除入口
- workflow 卡片当前应在“前往制作区”附近提供“执行历史”入口，打开后在中间弹窗查看该 workflow 的全部执行记录，并按执行类型分类展示“执行任务 / 执行对象 / 执行时间”
- 删除后对应 workflow 定义数据应从后端删除，并不再进入制作区 / 查看区 / catalog 暴露面
- workflow 画布页应以“画布优先”作为首要布局原则：删除右侧冗余辅助区后，让画布成为主视图，并支持全屏编辑
- workflow 创建失败若为编码冲突，前端应将 `WORKFLOW_CODE_ALREADY_EXISTS` 转换为可读提示，而不是直接暴露底层 500 异常

当前阶段必须新增：
- 独立审批工作区
- 审批意见输入
- 执行结果卡片 / 执行失败卡片
- 部门切换后的 workflow 查询与触发入口
- 语音 / PDF / 图片上传能力预留，但前端展示应后续并入输入框，不要求当前阶段单独露出卡片

对话工作台当前阶段建议拆分：
- `DepartmentWorkflowCatalog.vue`：按部门 + 职能分类查询 workflow
- `ApprovalWorkbench.vue`：审批任务区
- `ExecutionResultCard.vue`：执行结果展示
- `WorkflowParameterCard.vue`：workflow 缺参时的参数补齐卡片
- 多模态附件入口当前不再保留独立组件卡片，后续统一并入主输入框交互

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

### 4.4 RecordsWorkbenchPage.vue
负责：
- 查看 `dayan_mock_records` 中的真实业务表
- 选择数据源 / 表
- 新增 / 编辑 / 删除记录
- 触发标准数据库事件，驱动 `sensor_agent`
- 查看最近一次事件、感知命中、workflow 执行与写回结果

定位约束：
- `RecordsWorkbenchPage.vue` 是当前无 Go 正式表格能力时的临时测试页
- 当 Go 端正式表格与 records API 就绪后，该页面及其子组件允许整体删除

当前阶段必须新增：
- 独立 `RecordsWorkbenchPage.vue`
- 左侧数据源/表导航
- 中间真实表格区
- 编辑弹窗与行级操作
- 最近事件与执行结果侧栏

当前阶段交互口径：
- 业务表格区必须作为一级页面与其他工作台并列，不挂在监控区内部
- 页面默认连接 Python 提供的 Mock Records API，而不是直接连数据库
- 记录保存成功后，页面必须能看到真实写入结果，而不是只展示前端临时状态
- 记录编辑触发的标准事件必须可追踪到最近一次感知链路
- 该页面不应成为正式员工长期使用入口；正式入口后续由 Go 侧表格能力所在部门接管
- 右侧最近事件区当前应只保留“已实际触发 workflow”的事件索引，不再展示大量 `触发 execution：无` 的噪声卡片；卡片内容以表名、记录号、触发时间与 execution_id 为主

当前已落地的第一批实现：
- 顶部导航已新增 `业务表格区`
- `router/agentCollab.ts` 已注册 `/records-workbench`
- `RecordsWorkbenchPage.vue` 已实现首版三栏布局：左侧选表、中间真实表格、右侧最近事件流
- `api/records.ts` 与 `store/records.ts` 已落地，支持表列表、schema、行列表、创建、编辑、删除、最近事件刷新
- 右侧 `Recent Trigger Stream` 当前只保留为最近事件索引区，不再承担 execution 详情查看职责
- 当前页面仍是单文件集成实现，`components/records/*` 目录尚未拆出；后续若继续演进再做组件细分

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
- `pages/WorkflowCanvasPage.vue` 中的 mock event inject 对话框，用于以标准事件信封驱动 `sensor_agent -> decision_agent -> execution_agent` 联调

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
- 执行目标类型至少包含：`go_api`、`department_table`
- 当选择 `department_table` 时，前端需展示目标编码、底层 provider、写入动作、字段映射、默认值、幂等键模板配置
- 是否进入对话审批开关
- 审批卡片投递到对话工作区
- 执行结果回传到对话工作区
- `ExecutionConfigPanel.vue` 当前阶段应优先支持：目标模式、provider、route mode、字段映射、缺省值与幂等模板

节点设置弹窗当前交互口径：
- `NodeConfigPanel.vue` 负责统一外层壳层、节点元信息、基础信息与 JSON 高级配置
- 节点设置弹窗统一改为：浅色属性面板风格、左窄右宽两栏结构、低对比边框、分区式 section 布局
- `dialog_agent`、`sensor_agent`、`decision_agent`、`execution_agent` 必须使用专属 panel，不再把复杂字段直接挤在通用表单区
- `SensorConfigPanel.vue` 当前应覆盖：来源定义、触发条件、输出映射、是否保留原始 payload
- `SensorConfigPanel.vue` 当前应进一步明确数据库实时感知默认面向 `payload.after` 进行条件判断与字段映射，同时保留 `event.*` 读取原始事件信封的能力
- `SensorConfigPanel.vue` 当前应把触发条件改为结构化规则列表（字段、操作符、比较方式、固定值/字段对比），而不是多行手写表达式
- `DialogConfigPanel.vue` 当前应覆盖：入口提示、意图标签、响应风格、记忆强度
- `DecisionConfigPanel.vue` 当前应覆盖：决策模式、规则/模型/提示模板、约束列表、知识范围
- `DecisionConfigPanel.vue` 当前已进一步细化为三段式专属配置：
  - 规则型：`rule_set_ref / severity_thresholds / severity_field / action_type / target_item_field / quantity_field`
  - 模型型：`model_type / model_ref / optimization_goal / candidate_actions / objective_weights / capacity_limits`
  - 智能型：`prompt_template / output_template / constraints / rag_refs / include_explanation / include_citations`
- 三模式切换时应保留非当前模式字段，避免用户在来回切换时丢失已录入配置
- `ExecutionResultCard.vue` 当前除 `sensor_outputs` 外，也应开始展示 `decision_outputs`，便于浏览器级联调时直接看到决策摘要、风险等级与结构化 payload
- `ExecutionConfigPanel.vue` 当前应覆盖：执行策略、审批策略、目标注册与路由、写入映射
- 节点专属 panel 的目标不是“字段越多越好”，而是把配置拆成清晰分区，降低扫描成本与误配风险
- JSON 高级配置区下沉到左侧次级区块，作为调试/补充位点，而不是与正式配置并列抢主视觉

最新布局收口：
- 顶部第一排固定为：`基础信息 / 节点类型 / 节点 ID`
- 删除“画布位置”展示，避免占用首屏注意力
- 主要设置区统一改为自上而下的纵向排布，不再左右并列展开主配置
- `dialog / sensor / decision / execution / condition / approval / wait / exception` 当前都应使用同风格专属 panel
- JSON 高级配置统一置于最底部，作为调试区而不是主体内容

画布节点与连线当前交互口径：
- 节点卡片改为更清晰的白底高对比信息层级：类型 badge、节点 ID、节点名称、节点摘要分层展示
- 节点悬停时，左上角浮现删除按钮，可直接删除节点
- 连线悬停或选中时，连线中部附近浮现删除按钮，可直接删除该连线
- 删除交互不替代顶部全局删除按钮，但应作为更直接的画布内操作入口

WorkflowCanvas 当前阶段补充要求：
- 删除右侧 `Graph Utilities` 固定栏，避免压缩画布首屏编辑面积
- 顶部信息区收敛为紧凑型元信息 + 核心动作条
- 画布区保留：节点添加按钮、缩放控件、全屏编辑按钮、重置与删除动作

## 6. 前后端并行开发建议
- 前端先根据 `types/*.ts` 固定页面数据结构
- 画布页优先联调 `workflow-dsl.md` 对应的 `ui_schema`
- 对话页优先联调 `python-service-api.md` 与 `api-event-contracts.md`
- 监控页优先联调 `Monitor API` 和 SSE 事件

对话页还应优先联调：
- workflow 注册目录查询接口
- 审批工作区接口
- 多模态上传与消息归一化接口

审批工作区当前口径：
- `ApprovalWorkbench.vue` 不再是静态壳，而是负责：审批任务列表、选中任务、审批意见输入、同意/驳回提交
- `ApprovalCard.vue` 负责渲染真实审批任务标题、摘要、execution_id 与状态
- `useApprovals.ts` 负责拉取审批任务、提交审批、审批后续接 execution stream
- 审批工作区当前优先面向最小恢复链，不先扩展复杂筛选、批量处理或监控联动

对话工作台当前落地口径：
- `ChatWorkbenchPage.vue` 应明确表现为“部门员工的唯一对话工作台入口”，而不是普通拼装页面
- 会话列表、对话消息、审批任务、工作流目录、执行结果需要在同一工作台中可见
- 审批工作区与执行结果区属于对话工作台内部能力，而不是独立于对话之外的第二套入口
- 会话切换必须联动刷新：消息列表、工作流目录、审批任务
- `WorkflowCanvasPage.vue` 应提供明确的“进入对话工作台”入口，提示配置员：用户实际使用 workflow、处理审批与查看执行结果，应在独立对话工作台中完成

工作流查看区当前落地口径：
- `WorkflowLibraryPage.vue` 负责展示所有已制作 workflow 的统一查询入口
- 当前阶段优先支持：关键词搜索、发布状态筛选、所属部门筛选
- 该页面是“查看与进入”的入口，不承担 workflow 编辑本身

## 7. 合并进主 Vue 项目时的规则
- 保持 `agentCollab.ts` 为单独路由模块
- 页面入口保持在 `pages/`
- 不在模块内写死主系统菜单、主布局、全局权限实现
- 需要对接主系统时，只适配：路由注册、鉴权注入、HTTP client 注入
