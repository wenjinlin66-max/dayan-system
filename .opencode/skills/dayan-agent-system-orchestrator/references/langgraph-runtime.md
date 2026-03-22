# LangGraph 执行器设计

## 1. 目标
Python 执行器负责把 `workflow-dsl.md` 中定义的 `execution_dag` 编译为可运行的 LangGraph 工作流，并支持：
- 可恢复执行
- 审批中断 / 恢复
- 节点级错误处理
- 草稿沙盒与正式发布双模式执行
- 状态流式反馈

## 2. 内部模块划分

### 2.1 workflow_loader
- 根据 `workflow_id + version + mode` 加载执行版本
- 校验是否可执行（released 或 sandbox）
- 返回标准化的 `WorkflowSpec`

### 2.2 dag_compiler
- 将 `execution_dag` 编译为 LangGraph 节点图
- 建立节点依赖、entrypoint、异常跳转、子流程引用
- 校验是否存在非法环路、缺失 handler、未定义入口

### 2.3 state_store
- 管理 `execution_runs`、checkpoint、timeline、运行态变量
- 对接 LangGraph thread/checkpointer
- 保证 `execution_id == thread_id`

### 2.4 node_dispatcher
- 根据节点 `type` 查找对应 handler
- 负责注入标准上下文：
  - execution context
  - operator context
  - dept scope
  - memory accessors
  - tool registry

### 2.5 approval_manager
- 在审批节点或高风险执行动作前发起中断
- 写入审批运行态镜像
- 等待恢复请求并继续执行

### 2.6 event_bridge
- 消费 Go -> Python 事件
- 推送 Python -> 前端 SSE / WebSocket / 审计事件
- 保证事件 envelope 与 execution state 同步

### 2.7 error_router
- 统一捕获 handler 错误
- 根据节点配置跳转到 `exception` 节点或标记失败
- 输出错误日志和补偿上下文

## 3. LangGraph 状态模型
建议执行状态对象至少包含：

```json
{
  "execution_id": "exec_001",
  "workflow_id": "wf_purchase_approval",
  "workflow_version": 3,
  "mode": "released",
  "dept_id": "supply_chain",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "current_node": "decision_1",
  "history": [],
  "context": {},
  "decision_outputs": {},
  "tool_outputs": {},
  "approval": null,
  "metrics": {},
  "errors": []
}
```

## 4. 节点调度原则
- `sensor_agent`：负责接收并标准化输入事件
- `decision_agent`：输出结构化决策结果
- `execution_agent`：调用工具或 Go API，必要时触发审批
- `dialog_agent`：处理 ask / approve / command 三类入口
- `condition`：只做分支判断
- `parallel`：负责 fork/join 协调
- `loop`：负责循环次数或退出条件
- `subflow`：加载已发布子流程并执行
- `wait`：挂起等待时间或外部信号
- `approval`：触发 interrupt，等待 resume
- `exception`：处理失败后的兜底逻辑

> 说明：`monitor_agent` 不属于普通 execution_dag 节点调度范围，监控能力按独立控制平面实现。

## 5. handler 映射建议
| node_type | handler | 说明 |
|---|---|---|
| sensor_agent | `handle_sensor_node` | 输入采集与标准化 |
| decision_agent | `handle_decision_node` | 规则/模型/LLM 决策 |
| execution_agent | `handle_execution_node` | 工具调用 / Go API 执行 |
| dialog_agent | `handle_dialog_node` | 对话问答 / 命令解析 / 审批反馈 |
| condition | `handle_condition_node` | 条件分支 |
| parallel | `handle_parallel_node` | 并行 fork/join |
| loop | `handle_loop_node` | 循环控制 |
| subflow | `handle_subflow_node` | 子流程调度 |
| wait | `handle_wait_node` | 等待定时/外部信号 |
| approval | `handle_approval_node` | 人工审批中断 |
| exception | `handle_exception_node` | 异常处理 |

监控型智能体运行时建议单独实现于控制平面服务，而不是放入本表。

### 5.1 当前已落地的最小 runtime 主链
- `ExecutionService.start()` 不再只写入 `ExecutionRun`，而是在创建 execution 记录后立即触发一轮最小 runtime 执行
- `GraphBuilder` 当前已支持把 `execution_dag` 解析为：`entrypoint + node map + outgoing edges`
- `NodeDispatcher` 当前已接入：`sensor_agent`、`dialog_agent`、`decision_agent`、`condition`、`approval`、`execution_agent`
- `execution_agent` 当前通过 `ExecutionNodeHandler + ToolRegistry` 解析 `department_table` writer，不再在 runtime 中写死 mock writer
- `ToolRegistry.build_default()` 当前可根据配置创建 `DepartmentTableExecutor`，并在“真实 Go Records API / Mock fallback”之间切换
- `sensor_agent` 当前已支持：输入标准化、字段筛选、条件匹配、输出映射、感知结果回写到 runtime state
- `sensor_agent` 当前额外支持：来源匹配（`source_system / source_table / source_event_key`）以及“未命中时停止向下游传播”的 gating 语义
- `decision_agent` 当前已支持：`rule / model / llm` 三模式运行分支，并接入统一决策输出结构
- `decision_agent.rule` 当前不再是纯固定模板，而是会读取 `rule_set_ref / rule_config`，结合库存/阈值/建议数量等输入计算严重度、缺口和推荐动作
- `decision_agent.model` 当前不再是单一硬编码结果，而是会读取 `model_type / model_ref / optimization_goal / model_params`，对候选动作做确定性评分并输出推荐动作与评分明细
- `decision_agent.llm` 当前会通过统一 `LLMClient` 调用默认 OpenAI-compatible 模型网关（Gemini 中转站），结合知识/历史摘要、优化目标、约束条件与输出模板要求生成结构化决策 JSON；若网关异常则退回本地 fallback 结构
- `decision_agent` 当前三种模式最终都应归一为统一“执行束（execution bundle）”结构：顶层保留 `decision_summary / risk_level / explanation / recommended_actions`，`decision_payload` 内固定补齐 `chat_report` 与 `table_write` 两个子对象，供并行后的不同执行节点共享消费
- `dialog_agent` 当前已开始把输入写入上下文记忆与历史执行记忆，并会根据 `promptHint / intentTag / responseStyle / memoryProfile` 调用统一 `LLMClient` 生成节点级对话回复；`dialog_outputs` 中会保留 `reply_source / fallback_reason` 便于审计
- `execution_agent` 当前除手动选定第一目标外，还支持在 `execution_target_mode=ai_select` 且存在多个候选目标时，通过统一 `LLMClient` 做目标选择；若网关异常或返回非法目标，则退回第一候选目标
- `execution_agent` 当前已补齐 `result_delivery=chat` 的风险报告回传链：既支持 `department_table` 写入完成后把结构化结果整理为对话区报告，也支持在没有有效 `target_ref` 时进入 chat-only 模式，只基于 `decision_outputs` 生成 AI 风险报告并投递到目标部门对话框
- `execution_agent` 当前已进一步收口为“单目标执行器”运行时：显式支持 `target_type=department_chat` 与 `target_type=department_table` 两类主目标；`department_chat` 直接发送风险报告，`department_table` 负责表格写入，二者作为同级执行目标存在
- `department_chat` 执行节点当前优先消费 `decision_payload.chat_report`（`title/content/audience`）；`department_table` 执行节点当前优先消费 `decision_payload.table_write` 作为默认写表载荷，前端字段映射只做覆盖与补充
- `execution_agent` 的 `row_mapping` 当前除 `decision_payload.* / dept_id / risk_level` 外，已支持直接读取 `sensor_payload.*` 与 `event.*`；因此像 `parts_demand -> execution_agent` 这类“感知后直接写下游表”的 workflow 已可不经过 decision 节点直接完成结构化写表
- `execution_agent` 当前已扩展批量表格操作：`append_rows / upsert_rows / replace_rows`。其中 `replace_rows` 当前用于 `customer-order-parts-demand-projection`，先按 `order_no` 清理旧 `parts_demand` 与三张下游部门表，再批量写入新的需求记录，避免链路二继续依赖 service 硬编码投影
- `execution_agent` 当前已开始消费自身的 `approval_required / approval_mode`：命中风险审批后会在当前 execution 节点挂起，并将审批任务投递到对话审批工作区；审批通过后从当前 execution 节点恢复继续执行
- `parallel` 节点当前已从空壳推进到最小分支调度：可在 `decision -> parallel -> 多 execution_agent` 结构下依次推进多个并列分支，并与 execution 内部审批挂起/恢复链兼容；后续再继续增强为更完整的 fork/join 语义
- 三级记忆接口（context / history / knowledge）当前已以 runtime accessor 形式接入 handler
- `approval` 节点当前已支持：创建审批镜像任务、让 execution 进入 `waiting_approval`、并将恢复所需信息写入 execution context snapshot
- execution 终态写回 chat 时，当前优先消费执行型节点产出的 `tool_outputs[*].chat_delivery.content`；若未提供，则回退到通用状态文本
- execution 终态写回 chat 当前不再只投递单个会话：若已有来源 `session_id` 且部门匹配，则会保留来源会话；同时还会补发到该部门所有 active 的“当前部门主对话框”会话，保证 CEO 聚焦某部门与部门账号自己的主对话框都能看到同一条执行结果
- startup 当前已开始自动确保三条 released `parts_demand` 感知 workflow 存在：采购、生产、客户配合三条 fan-out 流程；它们统一走最小 DAG `sensor_agent(parts_demand) -> execution_agent(department_table)`
- startup 当前还会自动确保一条 released projection workflow 存在：`customer-order-parts-demand-projection`，运行形态为 `sensor_agent(customer_order) -> decision_agent(parts_demand_projection) -> execution_agent(replace_rows -> parts_demand)`
- 每经过一个节点，都会额外写入新的 `ExecutionCheckpoint`
- 终态会把 `history / context / dialog_outputs / sensor_outputs / decision_outputs / tool_outputs / errors` 回写到 `ExecutionRun.final_output`

当前阶段说明：
- 该链路属于 M4 的“最小可运行 runtime”
- 现阶段仍是同步执行，但 adapter 结构已经补齐：默认优先走 Go Records Client；若未配置 `GO_RECORDS_BASE_URL` 且允许 mock，则退回 `MockRecordsGateway`
- 当前智能体能力仍处于第一阶段：memory search 仍为本地 runtime 级实现；但 `decision_agent` 已从“三模式骨架”推进到“规则型可配置、模型型可评分、智能型真实 AI 调用”的细化运行链路
- 当前审批恢复链属于 Python 侧最小闭环：先以 mirror task + execution resume 为主，不依赖 Go 审批主记录联调
- 后续继续补异步 worker、更完整的异常路由，以及审批意见/时间线更细粒度记录

## 6. 执行生命周期
```text
load workflow -> build state -> compile graph -> invoke entrypoint
-> dispatch node handlers -> checkpoint after key transitions
-> interrupt if approval/wait needed -> resume -> continue
-> success/fail/cancel -> emit final state
```

## 7. 中断与恢复规则
- 审批节点必须持久化当前状态快照
- `resume` 只能恢复 `waiting_approval` 或 `waiting_signal` 状态
- 恢复请求必须带 `execution_id` 与合法的部门/操作人上下文
- 恢复后必须记录 timeline 事件

## 8. 异常恢复规则
- handler 抛错时先检查节点是否声明 `on_error`
- 若声明异常兜底节点，跳转执行该节点
- 若未声明，则将 execution 标记为 failed
- 所有失败都必须写入 `audit_logs` 与 `tool_run_logs`（如有）

## 9. 运行时边界
- LangGraph 只负责执行编排，不承载最终权限真相
- 权限检查必须在入口 API、恢复 API、数据访问适配层中完成
- 条件表达式真相以 Go 规则或统一编译产物为准，Python 不再发明第二套语义
