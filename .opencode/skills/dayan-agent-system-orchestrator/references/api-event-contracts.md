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
| /api/v1/workflows/:workflow_id/draft | PUT | 更新工作流草稿 | Python侧鉴权 | 是 |

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
| /api/v1/executions/:execution_id | GET | 查询执行状态 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/resume | POST | 恢复审批或等待中的执行 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/cancel | POST | 取消执行 | Python侧鉴权 | 是 |
| /api/v1/executions/:execution_id/timeline | GET | 查询执行时间线 | Python侧鉴权 | 是 |

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
| /api/v1/chat/sessions/:session_id/messages | POST | 发送对话消息/语音/PDF 指令 | Python侧鉴权 | 否 |
| /api/v1/chat/sessions/:session_id/messages | GET | 查询会话消息 | Python侧鉴权 | 是 |
| /api/v1/chat/sessions/:session_id/approvals | GET | 查询会话内审批卡片 | Python侧鉴权 | 是 |
| /api/v1/chat/workflows/catalog | GET | 按部门/职能查询可用 workflow 目录 | Python侧鉴权 | 是 |
| /api/v1/chat/route | POST | 对消息执行 ask/approve/command 路由 | Python侧鉴权 | 是 |

### 2.6 对话路由契约
对话型智能体不得只靠自由语言直接执行 workflow，必须走：
1. 意图分类：`ask | approve | command`
2. 若为 `command`，先查 workflow registry
3. 进行 `dept_id + role + required_inputs` 过滤
4. 若有多个候选且不明确，则返回候选列表请求用户确认

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
      "confidence": 0.82
    }
  ],
  "needs_confirmation": false,
  "missing_inputs": []
}
```

## 3. Python -> Go 泛型操作契约
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/records/:table_id | POST | 新增业务记录 | Go侧鉴权 | 视业务而定 |
| /api/v1/records/:table_id/:record_id | PUT | 修改业务记录 | Go侧鉴权 | 是 |
| /api/v1/records/:table_id/:record_id | DELETE | 删除业务记录 | Go侧鉴权 | 是 |
| /api/v1/records/:table_id/query | POST | 查询业务记录 | Go侧鉴权 | 是 |

## 3.1 Go -> Python 感知事件消费约束
- Go 是数据库变更事件的发布方
- Python 是感知订阅与条件匹配的消费方
- Python 第一阶段不直接做数据库 CDC，而是消费 Go 发布的业务事件
- Python 消费后应写入 `sensor_event_inbox`，再由 `sensor_subscriptions` 做匹配与分发

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

## 7.1 部门隔离原则
- 所有 Python 接口默认要求 `dept_id` 上下文
- 对话查询与工作流执行必须检查 workflow 授权部门范围
- 跨部门查询必须被拒绝或显式走更高权限通道

补充原则：
- workflow 注册目录查询也必须先按 `dept_id` 过滤
- 同部门不同账号默认同权，但所有 chat / approval / execution 记录必须按 `user_id` 留痕

## 8. 待确认项
- 
