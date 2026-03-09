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

### 2.5 对话入口接口
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/chat/sessions | POST | 创建对话会话 | Python侧鉴权 | 否 |
| /api/v1/chat/sessions/:session_id/messages | POST | 发送对话消息/语音/PDF 指令 | Python侧鉴权 | 否 |
| /api/v1/chat/sessions/:session_id/messages | GET | 查询会话消息 | Python侧鉴权 | 是 |
| /api/v1/chat/sessions/:session_id/approvals | GET | 查询会话内审批卡片 | Python侧鉴权 | 是 |

## 3. Python -> Go 泛型操作契约
| 接口 | 方法 | 说明 | 鉴权 | 幂等 |
|---|---|---|---|---|
| /api/v1/records/:table_id | POST | 新增业务记录 | Go侧鉴权 | 视业务而定 |
| /api/v1/records/:table_id/:record_id | PUT | 修改业务记录 | Go侧鉴权 | 是 |
| /api/v1/records/:table_id/:record_id | DELETE | 删除业务记录 | Go侧鉴权 | 是 |
| /api/v1/records/:table_id/query | POST | 查询业务记录 | Go侧鉴权 | 是 |

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

### 5.2 SSE 推送事件建议
- `execution.started`
- `execution.status_changed`
- `execution.waiting_approval`
- `execution.tool_called`
- `execution.finished`
- `approval.requested`
- `approval.resumed`

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

## 7.1 部门隔离原则
- 所有 Python 接口默认要求 `dept_id` 上下文
- 对话查询与工作流执行必须检查 workflow 授权部门范围
- 跨部门查询必须被拒绝或显式走更高权限通道

## 8. 待确认项
- 
