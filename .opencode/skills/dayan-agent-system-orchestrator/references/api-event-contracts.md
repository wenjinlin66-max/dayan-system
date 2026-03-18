# API 与事件契约模板

## 1. Go -> Python 事件上行契约
### 1.1 统一事件信封
```json
{
  "event_id": "",
  "event_type": "",
  "event_version": 1,
  "source": "",
  "occurred_at": "",
  "trace_id": "",
  "correlation_id": "",
  "causation_id": "",
  "dept_id": "",
  "tenant_id": "",
  "actor": {
    "user_id": "",
    "roles": [],
    "scopes": []
  },
  "workflow_id": "",
  "workflow_version": 0,
  "mode": "released",
  "subject": {
    "record_table_id": "",
    "record_id": "",
    "execution_id": ""
  },
  "idempotency_key": "",
  "payload": {}
}
```

### 1.2 事件类型建议
- `record.created`
- `record.updated`
- `record.deleted`
- `iot.status_reported`
- `third_party.notification_received`
- `supply_chain.exception_detected`
- `schedule.tick`
- `approval.resumed`
- `chat.command_received`
- `chat.query_received`

### 1.3 数据库实时感知第一阶段标准事件
第一阶段推荐以 Go 业务层发布的数据库/业务记录变更事件作为感知型智能体输入，Python 不直接直连 Go 业务库。

推荐事件示例：
```json
{
  "event_id": "evt_db_001",
  "event_type": "record.updated",
  "event_version": 1,
  "source": "go.records.gateway",
  "occurred_at": "2026-03-10T10:00:00Z",
  "trace_id": "trace_001",
  "correlation_id": "corr_001",
  "dept_id": "production",
  "tenant_id": "tenant_a",
  "actor": {
    "user_id": "u_001",
    "roles": ["operator"],
    "scopes": ["erp.production"]
  },
  "subject": {
    "record_table_id": "inventory_stock",
    "record_id": "stock_1001",
    "execution_id": ""
  },
  "idempotency_key": "inventory_stock:stock_1001:updated:2026-03-10T10:00:00Z",
  "payload": {
    "source_system": "ERP生产库",
    "table": "inventory_stock",
    "operation": "updated",
    "changed_fields": ["stock_count", "updated_at"],
    "before": {
      "item_id": "A-1001",
      "stock_count": 18,
      "safety_limit": 20,
      "warehouse_id": "W-01"
    },
    "after": {
      "item_id": "A-1001",
      "stock_count": 16,
      "safety_limit": 20,
      "warehouse_id": "W-01"
    }
  }
}
```

字段要求：
- `event_type`：`record.created | record.updated | record.deleted`
- `subject.record_table_id`：业务表标识
- `subject.record_id`：业务记录主键
- `payload.changed_fields`：变化字段列表
- `payload.before / after`：变更前后快照（至少 `after` 必填）
- `idempotency_key`：保证感知入箱去重

## 2. Python 工作流定义与发布契约
### 2.1 保存草稿
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/workflows | POST | 创建工作流草稿 | Python侧鉴权 | 否 |
| /api/v1/workflows | GET | 查询 workflow 列表，支持按部门或全量演示视图返回 | Python侧鉴权 | 是 |
| /api/v1/workflows/:workflow_id/draft | PUT | 更新工作流草稿 | Python侧鉴权 | 是 |

补充读取约束：
- `GET /api/v1/workflows` 返回中必须包含 `workflow_category`
- `GET /api/v1/workflows` 返回中应补充 `workflow_trigger_type`，用于明确当前 workflow 的触发逻辑分类
- `GET /api/v1/workflows` 当前支持 `dept_id` 和 `include_all` 查询参数：前者用于制作区按显式部门加载 workflow，后者用于查看区的“部门 → 触发逻辑”演示视图
- `GET /api/v1/workflows`、`GET /draft`、`GET /releases/current`、`GET /versions`、`PUT /draft`、`POST /publish` 必须按 `dept_id` 做后端硬限制
- 工作流查看区前端不再用“部门下拉筛选”承担越权防护职责

补充分类约束：
- 当前保存/发布阶段，`category` 字段先承载“触发逻辑分类”语义
- 触发逻辑分类至少支持：`dialog_trigger / event_trigger / schedule_trigger`
- 后续若部门分类口径稳定，再在查看区与目录侧扩展为“部门 → 触发逻辑”两层分类，而不是重新发明另一套平行字段

补充删除约束：
- `DELETE /api/v1/workflows/{workflow_id}` 采用真实删除语义
- 删除时应一并删除对应 workflow 定义数据：`workflow_registry`、`workflow_versions`、`workflows`
- 删除后该 workflow 应从制作区列表、工作流查看区、chat catalog 暴露面中消失

补充错误约束：
- 若 `POST /api/v1/workflows` 中的 `code` 与已有 workflow 重复，必须返回 `409 Conflict`
- 错误详情建议固定为 `WORKFLOW_CODE_ALREADY_EXISTS`，前端据此给出“工作流编码已存在”的可读提示

### 2.2 编译与发布
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/workflows/:workflow_id/compile | POST | 将 ui_schema 编译为 execution_dag | Python侧鉴权 | 是 |
| /api/v1/workflows/:workflow_id/publish | POST | 发布当前候选版本 | Python侧鉴权 | 是 |
| /api/v1/workflows/:workflow_id/releases/:version | GET | 查询指定发布版 | Python侧鉴权 | 是 |
| /api/v1/workflows/:workflow_id/releases/current | GET | 查询当前发布版 | Python侧鉴权 | 是 |
| /api/v1/workflows/:workflow_id/archive | POST | 归档工作流 | Python侧鉴权 | 是 |

### 2.3 启动执行
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/executions/start | POST | 按 workflow_id + version/mode 启动执行 | Python侧鉴权 | 是 |
| /api/v1/executions/inject/mock-event | POST | 以标准事件信封形态注入 mock 数据库事件，驱动感知型工作流 | Python侧鉴权 | 是 |
| /api/v1/executions/workflow/:workflow_id/history | GET | 查询指定 workflow 的执行历史摘要，供查看区/对话区历史查看器使用 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id | GET | 查询执行状态 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id | DELETE | 删除执行记录，并同步清理 checkpoint / 审批镜像 / Mock Records 事件引用 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/stream | GET | 以 SSE 推送执行状态快照 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/resume | POST | 恢复审批或等待中的执行 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/cancel | POST | 取消执行 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/timeline | GET | 查询执行时间线 | Python侧鉴权 | 是 |

### 2.3.1 临时 Mock Records API
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/records/sources | GET | 获取临时 Mock Records 来源列表 | Python侧鉴权 | 是 |
| /api/v1/records/tables | GET | 获取临时 Mock Records 表列表 | Python侧鉴权 | 是 |
| /api/v1/records/tables/:table_name/schema | GET | 获取表结构说明 | Python侧鉴权 | 是 |
| /api/v1/records/tables/:table_name/rows | GET | 获取表数据 | Python侧鉴权 | 是 |
| /api/v1/records/tables/:table_name/rows | POST | 新增记录并触发标准事件 | Python侧鉴权 | 否 |
| /api/v1/records/tables/:table_name/rows/:record_id | PUT | 更新记录并触发标准事件 | Python侧鉴权 | 是 |
| /api/v1/records/tables/:table_name/rows/:record_id | DELETE | 删除记录并触发标准事件 | Python侧鉴权 | 是 |
| /api/v1/records/events/recent | GET | 获取最近事件与触发 execution 摘要 | Python侧鉴权 | 是 |

补充触发约束：
- `POST/PUT/DELETE /api/v1/records/tables/*` 产生的被动事件，不应按当前登录用户的 `dept_id` 去筛选 workflow，而应扫描所有 `active + current release` 的 workflow 并按 `sensor_agent` 配置匹配
- 一旦命中某条 workflow，被动触发创建 execution 时应使用该 workflow 的 `owner_dept_id` 作为 execution 部门上下文
- 事件信封中的 `event.dept_id` 当前同样应写入命中 workflow 的 `owner_dept_id`，确保后续 chat/approval/result delivery 都回到该 workflow 所属部门主链

### 2.4 监控与运维接口
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/monitor/executions | GET | 查询执行运行列表 | Python侧鉴权 | 是 |
| /api/v1/monitor/metrics | GET | 查询监控指标 | Python侧鉴权 | 是 |
| /api/v1/monitor/deadletters | GET | 查询死信/失败任务 | Python侧鉴权 | 是 |
| /api/v1/monitor/incidents | GET | 查询 incident 列表 | Python侧鉴权 | 是 |
| /api/v1/monitor/incidents/:incident_id | GET | 查询 incident 详情 | Python侧鉴权 | 是 |
| /api/v1/monitor/incidents/:incident_id/actions | POST | 提交监控干预动作 | Python侧鉴权 | 是 |

### 2.5 对话入口接口
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/chat/sessions | POST | 创建对话会话 | Python侧鉴权 | 否 |
| /api/v1/chat/sessions/:session_id | DELETE | 删除对话会话及其消息 | Python侧鉴权 | 是 |
| /api/v1/chat/sessions/:session_id/messages | POST | 发送对话消息/语音/PDF 指令 | Python侧鉴权 | 否 |
| /api/v1/chat/sessions/:session_id/messages | GET | 查询会话消息 | Python侧鉴权 | 是 |
| /api/v1/chat/sessions/:session_id/approvals | GET | 查询会话内审批卡片 | Python侧鉴权 | 是 |
| /api/v1/chat/workflows/catalog | GET | 按部门/职能查询可用 workflow 目录 | Python侧鉴权 | 是 |
| /api/v1/chat/route | POST | 对消息执行 ask/approve/command 路由 | Python侧鉴权 | 是 |
| /api/v1/chat/sessions/:session_id/workflows/:workflow_id/start | POST | 从目录或候选确认结果中显式启动某条 workflow | Python侧鉴权 | 是 |

补充会话响应约束：
- `GET /api/v1/chat/sessions` 与 `POST /api/v1/chat/sessions` 返回中应包含 `dept_id` 与 `last_message_at`
- 对话工作台以前端“部门对话框 / 部门会话”为主组织单位，不按 workflow 维度暴露入口

补充消息回流约束：
- 当 execution 因 `approval` 节点进入等待审批时，应向当前 chat session 写入一条审批提醒消息
- 当审批被同意/驳回时，应向当前 chat session 写入一条审批结果消息
- 当 execution 进入 finished / failed / cancelled 终态时，应向当前 chat session 写入一条执行结果消息
- `chat/workflows/catalog` 当前默认应仅暴露 `dialog_trigger` 类型 workflow，且要经过 `allowed_roles` 过滤
- `chat/sessions/:session_id/messages` 与 `chat/sessions/:session_id/workflows/:workflow_id/start` 当前都支持 `include_all + dept_id` 组合；CEO 聚焦具体部门时应继续以该组合做 scope 校验，而不是退回 `dept_id=ceo`
- 对于 dialog-trigger workflow，聊天候选返回前当前已按 `workflow_id` 去重，发布新版本时也应同步让旧 `workflow_registry` 条目失活，避免同一 workflow 因历史 active 版本重复出现在候选列表中

### 2.6 对话路由契约
对话型智能体不得只靠自由语言直接执行 workflow，必须走：
1. 意图分类：`ask | approve | command`
2. 若为 `command`，先查 workflow registry
3. 进行 `dept_id + role + required_inputs` 过滤
4. 若有多个候选且不明确，则返回候选列表请求用户确认
5. 若 workflow 仅有一个高置信候选但 `required_inputs` 缺失，必须优先返回 `missing_inputs` 与参数补齐提示，不得直接执行并使用默认兜底值继续写表

路由响应示例：
```json
{
  "route_type": "command",
  "dept_id": "production",
  "candidate_workflows": [
    {
      "workflow_id": "wf_replenishment",
      "title": "补货申请流",
      "category": "inventory",
      "confidence": 0.82,
      "required_inputs": ["item_id", "quantity"],
      "input_schema": {
        "properties": {
          "item_id": {
            "title": "物料编码",
            "type": "string"
          },
          "quantity": {
            "title": "补货数量",
            "type": "number"
          }
        }
      }
    }
  ],
  "needs_confirmation": false,
  "missing_inputs": ["item_id", "quantity"]
}
```

候选确认启动请求示例：
```json
{
  "source": "candidate_confirmation",
  "source_message_id": "msg_candidate_001",
  "note": "用户点击候选 workflow 启动"
}
```

参数补齐后启动请求示例：
```json
{
  "source": "parameter_completion",
  "source_message_id": "msg_candidate_001",
  "note": "补齐参数后启动 workflow",
  "input_values": {
    "item_id": "A-1001",
    "quantity": 200,
    "reason": "库存低于安全库存"
  }
}
```

补充约束：
- 若 workflow registry 中声明了 `required_inputs`，则目录启动、候选确认启动、自动命令启动都必须先经过缺参校验
- 缺参时不得直接创建 execution，而是返回 `missing_inputs + candidate_workflows[0].input_schema`，由前端继续渲染参数补齐卡片
- 参数补齐后的再次启动，必须继续复用同一条 `chat/sessions/:session_id/workflows/:workflow_id/start` 接口
- `command` 路由当前应只面向 `dialog_trigger` workflow 做 registry 检索，检索字段至少包括：`title / summary / synonyms / example_utterances`
- registry 命中后，必须继续按 `dept_id / allowed_roles / required_inputs` 做过滤，不能只靠自然语言直接硬选

执行状态 SSE 示例：
```text
event: status
data: {"execution_id":"exec_001","status":"running","current_node":"execution_agent_1"}
```

## 3. Python -> Go 泛型操作契约
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/records/:table_id | POST | 新增业务记录 | Go侧鉴权 | 视业务而定 |
| /api/v1/records/:table_id/:record_id | PUT | 修改业务记录 | Go侧鉴权 | 是 |
| /api/v1/records/:table_id/:record_id | DELETE | 删除业务记录 | Go侧鉴权 | 是 |
| /api/v1/records/:table_id/query | POST | 查询业务记录 | Go侧鉴权 | 是 |

## 3.1 Python -> 部门表格写入契约

当执行型智能体选择 `department_table` 作为执行目标时，统一按如下请求/响应口径调用底层适配器或工具执行器。

请求示例：
```json
{
  "execution_id": "exec_001",
  "workflow_id": "wf_replenishment",
  "workflow_version": 3,
  "node_id": "execution_dept_register",
  "dept_id": "production",
  "operator_id": "u_001",
  "target_code": "dept_table.production.replenishment_register",
  "target_type": "department_table",
  "provider": "bitable",
  "operation": "append_row",
  "idempotency_key": "production:exec_001:execution_dept_register",
  "row_payload": {
    "物料编码": "A-1001",
    "仓库": "W-01",
    "建议补货量": 200,
    "风险等级": "medium"
  },
  "write_options": {
    "allow_duplicate": false,
    "return_row_id": true,
    "return_sheet_name": true
  }
}
```

响应示例：
```json
{
  "status": "succeeded",
  "target_code": "dept_table.production.replenishment_register",
  "provider": "bitable",
  "operation": "append_row",
  "dept_id": "production",
  "sheet_name": "生产部补货登记表",
  "row_id": "rec_001",
  "summary": "已写入生产部补货登记表",
  "trace_id": "toolrun_001"
}
```

字段约束：
- `dept_id` 必须与当前 execution 上下文一致，不得跨部门越权写入
- `target_code` 必须来自 `execution_target_registry` 的已启用目标
- `operation` 第一阶段至少支持 `append_row`
- `idempotency_key` 必须参与去重，避免重复插入
- 结果必须可回传到对话工作区，并写入审计日志与工具执行轨迹

## 3.2 Go -> Python 感知事件消费约束
- Go 是数据库变更事件的发布方
- Python 是感知订阅与条件匹配的消费方
- Python 第一阶段不直接做数据库 CDC，而是消费 Go 发布的业务事件
- Python 消费后应写入 `sensor_event_inbox`，再由 `sensor_subscriptions` 做匹配与分发

## 3.3 初期开发阶段的本地联调 / Mock 契约

在初期开发阶段，如果 Go 数据库、Go 泛型 API 或真实事件总线尚未接入，允许通过 **Mock Gateway / Sandbox Adapter** 验证 Python 工作流能力，但必须遵循与正式契约一致的字段口径。

原则：
- Mock 只替代“数据来源与执行落点”，不替代正式契约结构
- 感知型智能体仍消费与正式环境相同结构的事件信封
- 对话型/执行型智能体仍调用与正式环境一致的查询/写入抽象接口
- Mock 数据必须带 `dept_id`、`tenant_id`、`actor`、`trace_id`、`idempotency_key` 等关键字段，避免联调时漏掉权限与幂等问题

推荐两类 Mock 方式：

### A. 事件回放方式（验证感知型 + workflow 启动）
- 由 Python 本地提供 `mock event inject` 能力，将标准事件信封直接写入 `sensor_event_inbox`
- 事件结构必须与 `1.1 统一事件信封` 和 `1.3 数据库实时感知第一阶段标准事件` 保持一致
- 适用于验证：条件匹配、字段映射、workflow 启动、审批、结果回传

推荐注入请求示例：
```json
{
  "workflow_id": "wf_inventory_sensor",
  "version": 3,
  "mode": "released",
  "event_type": "record.updated",
  "source": "mock.gateway",
  "event": {
    "event_id": "evt_mock_001",
    "source_system": "mock_erp",
    "table": "inventory_stock",
    "operation": "updated",
    "changed_fields": ["stock_count"],
    "after": {
      "item_id": "A-1001",
      "stock_count": 16,
      "safety_limit": 20,
      "warehouse_id": "W-01"
    }
  }
}
```

当前阶段实现约束：
- Python 在 `inject/mock-event` 内部会将上述请求包装为统一 `trigger.type=event` 的 execution start 请求
- `sensor_agent` 默认对 `event.payload.after` 进行条件匹配与 `payload.*` 输出映射；若映射路径写为 `event.*`，则读取原始事件信封字段
- `source_system / source_table / source_event_key` 会参与第一轮来源匹配；只有来源命中且条件命中时，workflow 才继续向下游节点流转
- 若感知未命中，execution 允许以“无下游继续执行”的方式平滑结束，但 `final_output.sensor_outputs` 必须保留本次来源匹配/条件匹配结果

### B. Mock Records Gateway（验证对话型查询 + 执行型增删改）
- Python 本地增加 `mock records gateway` / `records API` 临时测试层，模拟 Go 泛型 records API 的响应
- query/create/update/delete 的请求结构、响应结构、错误码与幂等规则必须尽量与正式 Go API 对齐
- 适用于验证：对话型查询、执行型写入、审批恢复后执行、结果回传、审计留痕

推荐约束：
- Mock Gateway 内部可使用 JSON 文件、SQLite、本地 PostgreSQL 或内存仓库承载测试数据
- 但对外暴露的接口语义必须继续使用 `table_id / record_id / dept_id / operator / payload`
- 所有 Mock 写入都必须保留审计与工具调用轨迹，避免只验证“成功路径”

当前第一批实现补充：
- 已采用独立 PostgreSQL 数据库 `dayan_mock_records` 作为临时测试底座
- 服务启动时会自动确保 `dayan_mock_records` 存在，并初始化：`inventory_stock / production_order / device_status / sensor_change_log`
- 通过 `/api/v1/records/*` 修改记录时，Python 会自动生成 `record.created / record.updated / record.deleted` 事件并写入 `sensor_change_log`
- 事件会按 `source_system=dayan_mock_records + table_name + event_type` 匹配已发布 workflow 中的 `sensor_agent`，若命中则直接触发 execution
- 该层属于临时测试设施；Go 正式 records 能力接入后应整体删除，不作为正式产品模块保留
- 当前 `/api/v1/records/events/recent` 主要返回：`changed_fields / triggered_execution_ids / created_at`，尚未直接暴露 `source_matched / condition_matched / 写回结果摘要`

结论：
- 早期开发不要等 Go 数据库直连完成后再验证 workflow
- 应先以 **标准事件信封 + Mock Records Gateway** 把 Python 工作流、审批、对话、执行链路跑通
- 待 Go 真实接口就绪后，仅替换 adapter，不重写 workflow 与节点契约

## 4. 审批挂起 / 唤醒契约

### 4.1 Python -> 前端审批卡片事件
```json
{
  "event_type": "approval.requested",
  "execution_id": "",
  "workflow_id": "",
  "workflow_version": 0,
  "node_id": "",
  "dept_id": "",
  "go_approval_id": "",
  "payload": {
    "title": "",
    "summary": "",
    "risk_level": "medium",
    "proposed_action": {},
    "context_snapshot": {}
  }
}
```

第一阶段要求：
- 所有需要人工确认的执行方案统一通过该审批卡片事件进入对话工作区
- 对话工作台必须有独立审批区域消费该事件

### 4.2 前端 / Go -> Python 恢复执行
```json
{
  "go_approval_id": "",
  "decision": "approved",
  "comment": "",
  "operator_id": "",
  "dept_id": "",
  "resume_payload": {}
}
```

### 4.3 恢复执行响应
```json
{
  "execution_id": "",
  "status": "running",
  "resumed_at": "",
  "next_node": ""
}
```

## 5. 监控与状态同步契约

### 5.1 Python -> 前端执行状态事件
```json
{
  "event_type": "execution.status_changed",
  "execution_id": "",
  "workflow_id": "",
  "workflow_version": 0,
  "status": "running",
  "current_node": "",
  "timestamp": "",
  "metrics": {}
}
```

### 5.2 监控 incident 契约
```json
{
  "incident_id": "",
  "incident_type": "timeout",
  "severity": "high",
  "scope": "execution",
  "execution_id": "",
  "workflow_id": "",
  "status": "open",
  "summary": "执行超过阈值未完成",
  "payload": {},
  "created_at": ""
}
```

### 5.2.1 监控干预动作契约
```json
{
  "action": "pauseExecution",
  "operator_id": "",
  "reason": "timeout exceeded",
  "payload": {}
}
```

约束：
- 监控型智能体只能调用受控动作 API，不能直接绕过运行时状态机修改 execution
- 所有干预动作必须进入 `audit_logs`

### 5.3 执行结果回传契约
```json
{
  "event_type": "execution.result.delivered",
  "execution_id": "",
  "workflow_id": "",
  "workflow_version": 0,
  "status": "succeeded",
  "summary": "补货申请已创建并等待后续处理。",
  "result_payload": {},
  "error_message": null,
  "timestamp": ""
}
```

约束：
- 第一阶段执行结果必须可回传到对话工作区
- 若执行失败，`error_message` 必须明确返回给用户

### 5.2 SSE 推送事件建议
- `execution.started`
- `execution.status_changed`
- `execution.waiting_approval`
- `execution.tool_called`
- `execution.finished`
- `approval.requested`
- `approval.resumed`

## 5.3 决策型智能体输出契约
无论采用规则型、模型型还是智能型，决策结果都应输出统一结构。

推荐结构：
```json
{
  "decision_mode": "llm",
  "decision_summary": "检测到库存风险，建议发起补货并通知生产经理审批。",
  "decision_payload": {
    "severity": "high",
    "item_id": "A-1001",
    "warehouse_id": "W-01",
    "recommended_quantity": 200
  },
  "risk_level": "medium",
  "recommended_actions": [
    {
      "action_type": "create_replenishment_request",
      "params": {
        "item_id": "A-1001",
        "quantity": 200
      }
    },
    {
      "action_type": "notify_manager",
      "params": {
        "dept_id": "production"
      }
    }
  ],
  "explanation": "库存低于安全阈值且历史消耗上升，补货优先级上调。",
  "citations": [
    {
      "source": "kb_inventory_policy",
      "snippet": "安全库存不足时应优先创建补货申请。"
    }
  ]
}
```

约束：
- 规则型 / 模型型 / 智能型都必须输出统一字段集合
- `citations` 可在非智能型模式下为空数组
- `recommended_actions` 必须保持结构化，便于执行型智能体直接消费
- 执行型、审批型、对话型节点不得依赖某一种模式的私有返回格式

## 6. 错误码约定
| 错误码 | 含义 | 处理建议 |
|---|---|---|
| WORKFLOW_NOT_PUBLISHED | 工作流未发布 | 仅允许草稿沙盒模式执行或先发布 |
| WORKFLOW_SCHEMA_INVALID | 工作流编译失败 | 修正节点配置后重新编译 |
| WORKFLOW_VERSION_MISMATCH | 请求版本与当前版本不一致 | 刷新后重试 |

## 7. 权限边界
- Python 负责 workflow 草稿、发布、版本查询、执行启动的权限校验
- Python 负责对话工作台、监控工作台、工作流执行状态接口的权限校验
- Go 负责业务数据权限、审批主记录、泛型业务 API 权限

对于感知型数据库事件：
- Go 负责按业务权限生成合法变更事件
- Python 负责按 `dept_id + source_event_key + subscription` 再做第二层过滤
- 对于当前 MVP 的前端联调入口，WorkflowCanvasPage 可直接构造上述 mock event inject 请求，不要求配置员手工拼接 HTTP 请求

## 7.1 部门隔离原则
- 所有 Python 接口默认要求 `dept_id` 上下文
- 对话查询与工作流执行必须检查 workflow 授权部门范围
- 跨部门查询必须被拒绝或显式走更高权限通道

补充原则：
- workflow 注册目录查询也必须先按 `dept_id` 过滤
- 同部门不同账号默认同权，但所有 chat / approval / execution 记录必须按 `user_id` 留痕

## 8. 待确认项
- 
