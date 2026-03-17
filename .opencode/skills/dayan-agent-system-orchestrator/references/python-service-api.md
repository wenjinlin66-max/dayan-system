# Python 智能体协同服务 API 设计

## 1. 服务定位
Python 服务对外提供 5 类能力：
- workflow 设计与发布
- workflow 执行与恢复
- 对话入口
- 监控与运维
- 内部智能体运行支撑

## 2. API 分组

### 2.1 Workflow API
- `POST /api/v1/workflows`
- `GET /api/v1/workflows?dept_id=<dept>&include_all=true|false`
- `GET /api/v1/workflows/sensor-metadata`
- `PUT /api/v1/workflows/:workflow_id/draft`
- `POST /api/v1/workflows/:workflow_id/compile`
- `POST /api/v1/workflows/:workflow_id/publish`
- `GET /api/v1/workflows/:workflow_id/releases/current`
- `GET /api/v1/workflows/:workflow_id/releases/:version`

### 2.2 Execution API
- `POST /api/v1/executions/start`
- `GET /api/v1/executions/workflow/:workflow_id/history`
- `GET /api/v1/executions/:execution_id`
- `DELETE /api/v1/executions/:execution_id`
- `GET /api/v1/executions/:execution_id/stream`
- `GET /api/v1/executions/:execution_id/timeline`
- `POST /api/v1/executions/:execution_id/resume`
- `POST /api/v1/executions/:execution_id/cancel`

### 2.3 Chat API
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions/:session_id/messages`
- `GET /api/v1/chat/sessions/:session_id/messages`
- `GET /api/v1/chat/sessions/:session_id/approvals`
- `GET /api/v1/chat/workflows/catalog`
- `POST /api/v1/chat/route`
- `POST /api/v1/chat/sessions/:session_id/workflows/:workflow_id/start`

### 2.4 Monitor API
- `GET /api/v1/monitor/executions`
- `GET /api/v1/monitor/metrics`
- `GET /api/v1/monitor/deadletters`

### 2.5 Mock Records API（临时测试层）
- `GET /api/v1/records/sources`
- `GET /api/v1/records/tables`
- `GET /api/v1/records/tables/:table_name/schema`
- `GET /api/v1/records/tables/:table_name/rows`
- `POST /api/v1/records/tables/:table_name/rows`
- `PUT /api/v1/records/tables/:table_name/rows/:record_id`
- `DELETE /api/v1/records/tables/:table_name/rows/:record_id`
- `GET /api/v1/records/events/recent`

## 3. 启动执行请求示例
```json
{
  "workflow_id": "wf_purchase_approval",
  "version": 3,
  "mode": "released",
  "trigger": {
    "type": "event",
    "event_id": "evt_001"
  },
  "dept_id": "supply_chain",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "input": {}
}
```

## 4. 执行状态响应示例
```json
{
  "execution_id": "exec_001",
  "workflow_id": "wf_purchase_approval",
  "workflow_version": 3,
  "mode": "released",
  "status": "running",
  "current_node": "decision_1",
  "thread_id": "exec_001",
  "dept_id": "supply_chain",
  "started_at": "2026-03-10T10:00:00Z",
  "updated_at": "2026-03-10T10:00:03Z"
}
```

## 5. 鉴权原则
- Workflow API：仅流程配置员/架构师可访问
- Execution API：需同时检查 workflow 授权范围与部门权限
- Chat API：部门用户可访问自己的对话与审批
- Monitor API：仅运维/管理员可访问全局视图

## 6. 调用方边界
- 前端画布工作台：主要调用 Workflow API
- 前端对话工作台：主要调用 Chat API 与部分 Execution API
- 前端监控工作台：主要调用 Monitor API
- Go 后端：主要通过 Redis 事件与 Python 交互，必要时调用 Execution / Resume 接口

### 6.1 对话型智能体补充说明
- `chat/workflows/catalog`：返回当前部门与当前账号可见的 workflow 目录
- `chat/route`：返回 `ask / approve / command` 的路由结果，不直接绕过 registry 执行 workflow
- `chat/sessions/:session_id/workflows/:workflow_id/start`：用于“目录点击启动”或“候选 workflow 二次确认后启动”；若 workflow 声明了 `required_inputs` 且请求未补齐，则先回写参数补齐消息，不直接创建 execution

### 6.1.1 workflow 目录返回字段补充
- `required_inputs`：当前 workflow 启动前必须补齐的字段名列表
- `input_schema`：字段标题、类型、说明与前端渲染建议
- 前端需复用同一条启动逻辑，覆盖目录启动、候选确认启动、参数补齐后启动三条路径

### 6.1.2 参数补齐启动请求示例
```json
{
  "source": "parameter_completion",
  "source_message_id": "msg_param_001",
  "note": "补齐参数后启动工作流：补货申请流",
  "input_values": {
    "item_id": "A-1001",
    "quantity": 200,
    "reason": "库存低于安全库存"
  }
}
```

### 6.2 执行状态流补充说明
- `executions/:execution_id/stream`：以 SSE 方式推送 execution 状态快照
- 当前前端策略为：优先 SSE；若流断开，则回退到轮询 `GET /executions/:execution_id`

## 7. Workflow 创建接口补充说明
- `POST /api/v1/workflows` 在 `code` 与现有 workflow 重复时，应返回 `409 Conflict`
- 错误详情当前使用：`WORKFLOW_CODE_ALREADY_EXISTS`
- 前端默认不应再固定写死容易重复的 demo code，而应生成新的草稿编码或提示用户调整编码
- `POST /api/v1/workflows` 当前允许显式传入 `owner_dept_id`，用于在制作区选择 workflow 归属部门
- `GET /api/v1/workflows` 当前支持 `include_all=true` 的演示期全量查看口径，供查看区实现“部门 → 触发逻辑”两层分组；正式账号权限收口后再切回严格按账号/部门控制

## 8. Execution API 当前行为补充
- `POST /api/v1/executions/start` 当前阶段会在创建 execution 后立即触发一轮最小 runtime 执行，而不是只生成 `running` 初始记录
- 若 graph 中包含 `dialog_agent -> decision_agent -> execution_agent` 这类最小链路，execution 结果会同步回填到 `final_output`
- `GET /api/v1/executions/:execution_id/stream` 因此不再只看到静态 `running`，而会读到已完成后的终态快照
- `DELETE /api/v1/executions/:execution_id` 当前会按 `dept_id` 做权限校验，并同步清理 `execution_runs`、`execution_checkpoints`、审批任务镜像，以及 Mock Records 最近事件中的 `triggered_execution_ids` 引用
- `GET /api/v1/executions/workflow/:workflow_id/history` 当前返回 workflow 级执行历史摘要，面向查看区与对话区历史查看器；除 `execution_type / task_summary / target_summary / started_at / updated_at` 外，还会返回 `result_status / result_summary / result_details[]`，用于展示“是否成功 / 改了什么 / 写入了哪些字段值”
- `POST /api/v1/executions/inject/mock-event` 当前使用 FastAPI `BackgroundTasks` 在返回 `execution_id` 后继续后台推进 execution；不再使用 `asyncio.create_task(...)` 直接裸起任务，以降低 Windows/本地开发态下 mock inject 续跑失效的概率
- runtime 在持久化 `final_output` 与 checkpoint 时，当前会对 `history / context / sensor_outputs / decision_outputs / tool_outputs / errors` 做独立快照，避免 JSON 字段因复用原始引用而出现“current_node 已推进，但 final_output 仍为空”的脏写现象
- 业务表格区自动触发 workflow 时，当前对 `source_system` 做临时兼容：`dayan_mock_records` 产生的表格变更事件可匹配配置为 `erp_prod` 的感知 workflow，便于配置员在临时测试表上验证正式 ERP 风格的低库存流程
- 对于 `result_delivery=chat` 的执行节点，当前不再强依赖已有 `trigger.session_id`；若 execution 是事件触发且没有 chat session，后端会自动复用或创建“当前用户 + 目标部门”的主对话会话，并把 execution result 以 `message_kind=execution_result` 系统消息追加进去
- `GET /api/v1/chat/sessions` 当前支持 `include_all=true` 与 `dept_id` 组合；仅当请求角色包含 `ceo` 时才允许跨部门读取全部门会话，普通部门账号仍按 `dept_id + user_id` 严格隔离
- `GET /api/v1/chat/sessions/{session_id}/messages` 当前已支持 CEO 读取跨部门会话消息；普通部门账号仍只能读取自己的部门会话
- `POST /api/v1/chat/sessions/{session_id}/messages` 当前已支持 `dept_id + include_all` scope 参数；CEO 在聚焦具体部门会话时发消息，会先按 scope 校验会话，再以该会话所属部门继续写入消息与执行路由，不再因为 token 自身 `dept_id=ceo` 而返回 404
- `POST /api/v1/chat/sessions/{session_id}/workflows/{workflow_id}/start` 当前也已支持 `dept_id + include_all` scope 参数，保证 CEO 在具体部门会话里可直接启动该部门 workflow
- `GET /api/v1/chat/workflows/catalog` 与 `GET /api/v1/approvals` 当前也支持 `include_all=true` + `dept_id` 范围过滤，用于 CEO 对话总览下查看全部门 workflow 目录与审批待办
- `ChatMessageResponse` 当前已稳定返回 `created_at`；前端消息流可直接按返回时间展示历史消息时间戳
- 请求上下文当前会从 `x-roles` 头解析角色列表；前端已使用账号身份面板动态注入 `x-user-id / x-dept-id / x-roles`
- 当前已新增认证接口：
  - `POST /api/v1/auth/login`：输入静态原型账号 `username/password`，返回 bearer token 与身份信息（`user_id / dept_id / display_name / roles`）
  - `GET /api/v1/auth/me`：基于 bearer token 返回当前身份上下文
- `get_request_context` 当前优先从 `Authorization: Bearer <token>` 解析 `user_id / dept_id / display_name / roles`；仅在未登录时才回退到旧的 header 兼容路径
- `GET /api/v1/executions/{execution_id}/stream` 当前已支持 `access_token` query 参数，解决前端 `EventSource` 不能发送 Authorization header 的问题
- `GET /api/v1/executions/workflow/{workflow_id}/history?include_all=true` 与 `GET /api/v1/workflows?include_all=true` 当前均已增加 CEO 角色门禁，普通账号不能用 crafted request 越权看全部门
- CEO 单部门查看当前通过 `include_all=true + dept_id=<目标部门>` 工作：`/v1/chat/sessions`、`/v1/chat/sessions/{id}/messages`、`/v1/chat/workflows/catalog`、`/v1/approvals`、`/v1/executions/{id}` 与 `/v1/executions/{id}/stream` 都已支持这种 CEO 聚焦部门口径
- chat workflow 目录当前在 service 层按 `workflow_id` 去重，避免 `workflow_registry` 中历史版本/重复有效行导致 CEO 目录重复显示同一 workflow 多次

### 8.1 department_table adapter 当前行为
- `execution_agent` 不再直接内嵌 mock writer，而是通过 `ToolRegistry` 解析 `department_table` writer
- 若已配置 `GO_RECORDS_BASE_URL`，则通过 `GoRecordsClient` 调用 Go 泛型 records API
- 若未配置 `GO_RECORDS_BASE_URL` 且 `ENABLE_MOCK_RECORDS_GATEWAY=true`，则退回 `MockRecordsGateway`
- `department_table` adapter 当前会保留：`tenant_id / dept_id / operator / trace_id / idempotency_key / payload / execution_context`
- 当 `execution_target_mode=ai_select` 且存在多个 `execution_targets` 时，`execution_agent` 当前会通过统一 `LLMClient` 从候选目标中选择 `target_ref`；若网关异常或返回无效目标，则退回第一候选目标，并在 `tool_outputs` 中记录 fallback 原因

### 8.2 智能体 runtime 当前行为
- `dialog_agent` 当前会根据节点配置中的 `promptHint / intentTag / responseStyle / memoryProfile` 调用统一 `LLMClient` 生成节点级对话回复，并把结果写入 `dialog_outputs` 与 context memory；`dialog_outputs` 当前至少包含 `message / reply / reply_source / llm_enabled / fallback_reason`
- `sensor_agent` 会将标准化后的感知结果写入 `sensor_outputs` 与 context memory，并记录 `source_matched / condition_matched / triggered / sensor_event`
- `decision_agent` 会输出统一结构：`decision_mode / decision_summary / decision_payload / risk_level / recommended_actions / explanation / citations`
- `decision_agent.rule` 当前会读取 `rule_set_ref / rule_config`，输出可直接被下游执行节点消费的严重度、缺口与推荐动作
- `decision_agent.model` 当前会读取 `model_type / model_ref / optimization_goal / model_params`，计算候选动作评分、推荐动作与建议数量，不再返回固定数量模板
- `decision_agent.llm` 当前会通过统一 `LLMClient` 请求 OpenAI-compatible 模型网关，并要求返回结构化 JSON；提示中会显式带入 `optimization_goal / constraints / output_template / include_explanation / include_citations`，若模型不可用，则退回本地 fallback 结构
- `dialog_agent` / `decision_agent` 当前会把关键摘要写入 history memory
- `final_output` 当前已开始包含：`history / context / dialog_outputs / sensor_outputs / decision_outputs / tool_outputs / errors`
- `sensor_agent` 若未命中来源或条件，当前 runtime 会在该节点停止向下游传播，不再默认沿第一条边继续执行

### 8.2.1 感知元数据目录当前行为
- 新增 `GET /api/v1/workflows/sensor-metadata`
- 该接口返回：来源类型、来源系统、表/数据域、事件键、字段、支持的比较操作符
- 前端 `SensorConfigPanel` 当前应默认基于该接口渲染来源选择与结构化条件配置，不再要求配置员手写整段条件文本

### 8.3 Mock Event Injector 当前行为
- 新增 `POST /api/v1/executions/inject/mock-event`
- 该接口用于在未接入 Go 真实事件流前，直接以 mock event 触发 workflow execution
- 请求可携带：`workflow_id / version / mode / dept_id / event_type / source / event / input_values / knowledge_docs`
- 该接口会把事件包装为 `trigger.type=event`，并把 mock event 写入 runtime input，供 `sensor_agent` 读取
- 若目标 workflow 版本未编译成功，当前接口必须返回 `WORKFLOW_NOT_COMPILED`
- mock 包装后的事件当前会补齐根级 `event_id`，便于 `sensor_outputs.sensor_event` 回写调试信息

### 8.4 Mock Records 临时测试层当前行为
- 服务启动时会优先确保独立数据库 `dayan_mock_records` 存在；若数据库不存在且账号具备权限，则自动创建
- 服务启动后会初始化三张测试业务表并补充首批种子数据：`inventory_stock / production_order / device_status`
- `records` API 当前支持：表列表、schema、行列表、创建、更新、删除、最近事件
- 当前记录修改会写入 `sensor_change_log`，并基于 `source_system=dayan_mock_records + table_name + event_type` 匹配已发布 workflow 中的 `sensor_agent`
- 若命中 workflow，会直接通过 `ExecutionService.start()` 触发 execution，并把 execution_id 回写到最近事件流中
- 该层属于临时测试设施；Go 正式 records 能力接入后应整体删除

## 9. Approval API 当前行为
- `GET /api/v1/approvals`：返回当前待审批任务列表，供 ApprovalWorkbench 拉取展示
- `POST /api/v1/approvals/resume`：接收 `execution_id / go_approval_id / decision / comment`，把 execution 从 `waiting_approval` 继续恢复或终止
- 当前实现为 Python 侧最小 mirror：审批任务镜像表仅保留最小字段，审批标题、摘要、next_node 等恢复信息写入 execution context snapshot
