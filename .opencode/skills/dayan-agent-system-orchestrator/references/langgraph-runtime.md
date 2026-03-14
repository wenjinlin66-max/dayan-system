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
- `decision_agent` 当前已支持：`rule / model / llm` 三模式最小骨架，并接入统一决策输出结构
- `dialog_agent` 当前已开始把输入写入上下文记忆与历史执行记忆
- 三级记忆接口（context / history / knowledge）当前已以 runtime accessor 形式接入 handler
- `approval` 节点当前已支持：创建审批镜像任务、让 execution 进入 `waiting_approval`、并将恢复所需信息写入 execution context snapshot
- 每经过一个节点，都会额外写入新的 `ExecutionCheckpoint`
- 终态会把 `history / context / sensor_outputs / decision_outputs / tool_outputs / errors` 回写到 `ExecutionRun.final_output`

当前阶段说明：
- 该链路属于 M4 的“最小可运行 runtime”
- 现阶段仍是同步执行，但 adapter 结构已经补齐：默认优先走 Go Records Client；若未配置 `GO_RECORDS_BASE_URL` 且允许 mock，则退回 `MockRecordsGateway`
- 当前智能体能力仍属于第一阶段骨架：memory search 为本地 runtime 级实现，LLM / model 模式仍是可运行骨架而非真实推理服务
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
