# Go ↔ Python 数据与事件契约总表 v1

## 1. 文档定位

本文档用于冻结“大衍天工·多智能体协同系统”中 **Go 数据底座** 与 **Python AI 中枢** 之间的正式协作边界，作为后续开发、联调、Mock 验证、契约测试与发布门禁的事实源。

适用范围：
- Go 负责业务数据、泛型 records API、权限主权、审批主记录、业务事件发布
- Python 负责 workflow 定义、版本管理、执行编排、智能体运行时、审批恢复、结果回传

本文档不定义 Go 内部实现细节（如 gin/gorm/goqu/jsonschema/expr 的具体代码写法），只定义 **跨服务稳定契约**。

## 2. 总体边界与主权划分

### 2.1 Go 主权范围
- 企业业务主数据
- 企业租户与部门主权信息
- 业务数据增删改查泛型 API
- 审批主记录
- 业务事件标准化与对外发布
- 业务数据访问鉴权与权限裁决

### 2.2 Python 主权范围
- workflow 草稿、发布版、执行 DAG 的真相源
- workflow 启动、执行、恢复、取消、时间线查询
- 五类智能体运行时
- 对话入口、审批镜像、结果回传
- 监控工作台与运行态审计聚合

### 2.3 明确禁止事项
- Python 不直连 Go 业务数据库
- Python 不自行监听 Go 业务数据库 CDC
- Go 不负责 workflow JSON 的真相存储与 DAG 编译执行
- 对话型智能体不得绕过 workflow registry 直接硬启动 workflow

## 3. 统一上下文契约（Auth Context / Runtime Context）

所有 Go ↔ Python 请求、事件、审批恢复、执行写入至少携带以下上下文：

```json
{
  "tenant_id": "tenant_a",
  "dept_id": "production",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"],
    "scopes": ["records.read", "records.write", "workflow.start"]
  },
  "trace_id": "trace_001",
  "correlation_id": "corr_001",
  "idempotency_key": "optional-but-recommended"
}
```

约束：
- `dept_id` 是默认隔离字段
- `tenant_id` 在多租户场景下必须显式传递
- Python 传递上下文不等于 Go 直接信任；Go 仍需自行校验权限
- `trace_id` 与 `correlation_id` 必须贯穿事件、执行、审批与工具调用主链

## 4. Records API 正式契约

Go 对 Python 暴露的统一 records API 如下：

| 接口 | 方法 | 作用 |
|---|---|---|
| `/api/v1/records/:table_id` | POST | 新增业务记录 |
| `/api/v1/records/:table_id/:record_id` | PUT | 修改业务记录 |
| `/api/v1/records/:table_id/:record_id` | DELETE | 删除业务记录 |
| `/api/v1/records/:table_id/query` | POST | 查询业务记录 |

### 4.1 Create

请求示例：

```json
{
  "tenant_id": "tenant_a",
  "dept_id": "production",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "payload": {
    "item_id": "A-1001",
    "quantity": 200,
    "reason": "库存低于安全阈值"
  },
  "idempotency_key": "production:replenishment:create:A-1001:200"
}
```

响应示例：

```json
{
  "table_id": "replenishment_requests",
  "record_id": "req_9001",
  "status": "created",
  "version": 1,
  "trace_id": "trace_001"
}
```

### 4.2 Update

请求示例：

```json
{
  "tenant_id": "tenant_a",
  "dept_id": "production",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "update_mode": "merge",
  "version": 3,
  "payload": {
    "status": "approved"
  },
  "idempotency_key": "production:replenishment:update:req_9001:approved"
}
```

约束：
- `update_mode` 第一阶段推荐支持 `merge`
- 若启用乐观锁，则 `version` 必须参与校验
- 更新成功后必须触发标准记录变更事件

### 4.3 Delete

请求示例：

```json
{
  "tenant_id": "tenant_a",
  "dept_id": "production",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "delete_mode": "soft",
  "idempotency_key": "production:replenishment:delete:req_9001"
}
```

约束：
- 第一阶段默认 `soft delete`
- 删除成功后仍应产生 `record.deleted` 事件或等价业务事件

### 4.4 Query

请求示例：

```json
{
  "tenant_id": "tenant_a",
  "dept_id": "production",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "select": ["item_id", "stock_count", "safety_limit", "updated_at"],
  "filters": [
    {
      "field": "item_id",
      "op": "eq",
      "value": "A-1001"
    }
  ],
  "sorts": [
    {
      "field": "updated_at",
      "order": "desc"
    }
  ],
  "page": 1,
  "page_size": 20
}
```

响应示例：

```json
{
  "table_id": "inventory_stock",
  "items": [
    {
      "record_id": "stock_1001",
      "item_id": "A-1001",
      "stock_count": 16,
      "safety_limit": 20,
      "updated_at": "2026-03-11T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "trace_id": "trace_001"
}
```

## 5. Query DSL 约束

### 5.1 第一阶段推荐字段
- `select`
- `filters`
- `sorts`
- `page`
- `page_size`
- `keyword`（可选）
- `include_deleted`（可选）

### 5.2 第一阶段推荐操作符
- `eq`
- `ne`
- `gt`
- `gte`
- `lt`
- `lte`
- `in`
- `contains`
- `starts_with`

### 5.3 编译原则
- Go 内部可使用 `goqu` 编译 SQL
- Python 与前端不感知 Go 内部 SQL 拼装细节
- 所有字段、操作符必须走 metadata 白名单，不允许自由拼接

## 6. Metadata Contract

Python 与前端在动态数据层场景下，需要通过 metadata 理解表结构，而不是猜测 Go 数据模型。

### 6.1 Table Metadata 最小字段
- `table_id`
- `display_name`
- `dept_scope`
- `schema_version`
- `primary_key`
- `soft_delete_enabled`
- `json_schema`
- `queryable_fields`
- `sortable_fields`

### 6.2 Field Metadata 最小字段
- `field`
- `type`
- `required`
- `default`
- `enum_values`
- `queryable`
- `sortable`
- `writable`
- `sensitive`

### 6.3 作用
- 对话型智能体可安全做数据查询
- 执行型智能体可安全构造写入 payload
- 感知型节点可理解字段过滤与映射边界

## 7. Go → Python 事件契约

### 7.1 Event Envelope v1

```json
{
  "event_id": "evt_001",
  "event_type": "record.updated",
  "event_version": 1,
  "source": "go.records.gateway",
  "occurred_at": "2026-03-11T10:00:00Z",
  "trace_id": "trace_001",
  "correlation_id": "corr_001",
  "causation_id": "",
  "tenant_id": "tenant_a",
  "dept_id": "production",
  "actor": {
    "user_id": "u_001",
    "roles": ["manager"],
    "scopes": ["erp.production"]
  },
  "subject": {
    "record_table_id": "inventory_stock",
    "record_id": "stock_1001",
    "execution_id": ""
  },
  "schema_version": "records-event-v1",
  "idempotency_key": "inventory_stock:stock_1001:updated:2026-03-11T10:00:00Z",
  "payload": {
    "operation": "updated",
    "changed_fields": ["stock_count"],
    "before": {
      "stock_count": 18
    },
    "after": {
      "stock_count": 16,
      "safety_limit": 20
    }
  }
}
```

### 7.2 事件类型建议
- `record.created`
- `record.updated`
- `record.deleted`
- `approval.resumed`
- `chat.command_received`
- `chat.query_received`

### 7.3 事件语义要求
- `before / after` 至少 `after` 必填
- `changed_fields` 用于感知型节点快速判断命中条件
- `event_id` 全局唯一
- `idempotency_key` 用于去重

## 8. 事件传输契约

### 8.1 正式原则
- Go 负责发布标准业务事件
- Python 负责消费并写入 `sensor_event_inbox`
- 不要求 Python 直接消费 Go 内部任务实现细节

### 8.2 当前约束
- 当前文档仅冻结“事件 envelope 与消费语义”
- 若 Go 内部使用 Asynq/Redis，也必须通过稳定的跨服务投递桥输出给 Python

### 8.3 必须明确的投递语义
- 至少一次投递（at-least-once）
- Python 消费侧必须支持幂等去重
- 失败消息需要重试与死信策略
- 所有消息必须保留 `trace_id / correlation_id`

## 9. Python Workflow 执行契约

### 9.1 Execution Start

```json
{
  "workflow_id": "wf_replenishment_apply",
  "version": 3,
  "mode": "released",
  "trigger": {
    "type": "chat",
    "session_id": "chat_001",
    "message_id": "msg_001"
  },
  "dept_id": "production",
  "operator": {
    "user_id": "u_001",
    "roles": ["manager"]
  },
  "input": {
    "item_id": "A-1001",
    "quantity": 200
  }
}
```

### 9.2 Execution 状态查询
- 查询 execution 当前状态
- 返回 `current_node / status / updated_at / final_output`

### 9.3 Resume
- 审批或等待节点恢复时使用
- 恢复请求必须携带审批结果或恢复输入
- 恢复后必须保证不会重复写入同一次业务动作

## 10. 对话型智能体与 workflow 触发契约

### 10.1 选流主链
- `ask / approve / command` 先分类
- `command` 必须先查 `workflow_registry`
- 再按 `dept_id + role + required_inputs + risk_level` 过滤
- 候选歧义时必须二次确认

### 10.2 启动主链
- 参数补齐后组装 execution start payload
- 调用 Python execution 启动入口
- 执行状态、审批卡片、最终结果回传到 chat

## 11. Approval & Resume 契约

### 11.1 主权划分
- Go：审批主记录系统
- Python：审批运行态镜像与 workflow 恢复控制

### 11.2 Python 镜像字段
- `go_approval_id`
- `execution_id`
- `node_id`
- `status`
- `snapshot`
- `resume_payload`

### 11.3 恢复原则
- 同一个 `go_approval_id` 只能对应一个有效恢复动作
- 恢复成功后 execution 状态必须更新
- 审批通过后的写入动作必须满足幂等

## 12. Error Code Contract

第一阶段统一错误码建议：

| 错误码 | 含义 |
|---|---|
| `TABLE_NOT_FOUND` | 目标表不存在 |
| `SCHEMA_NOT_FOUND` | metadata/schema 不存在 |
| `VALIDATION_FAILED` | JSON Schema 或业务校验失败 |
| `PERMISSION_DENIED` | 权限不足 |
| `RECORD_NOT_FOUND` | 目标记录不存在 |
| `VERSION_CONFLICT` | 乐观锁冲突 |
| `QUERY_NOT_ALLOWED` | 非法查询字段或操作 |
| `IDEMPOTENCY_CONFLICT` | 幂等键冲突 |
| `WORKFLOW_NOT_FOUND` | workflow 不存在或不可见 |
| `APPROVAL_RESUME_CONFLICT` | 审批恢复冲突 |
| `INTERNAL_ERROR` | 系统内部错误 |

错误响应建议：

```json
{
  "error_code": "VALIDATION_FAILED",
  "message": "field quantity is required",
  "details": {
    "field": "quantity"
  },
  "trace_id": "trace_001"
}
```

## 13. Mock Contract

### 13.1 原则
- Mock 只替代数据源与落点，不替代正式契约结构
- Mock 必须保留 `tenant_id / dept_id / operator / trace_id / idempotency_key`

### 13.2 两类 Mock
- `Mock Event Injector`：模拟 Go → Python 事件注入
- `Mock Records Gateway`：模拟 Go records API

### 13.3 作用
- 在 Go 真实库与真实接口未接入前，先验证 Python 的 workflow、对话、审批、执行主链
- 待正式 Go 接口上线后，仅替换 adapter，不重写 workflow 契约

## 14. 开发与联调使用规则

1. 先冻结本契约，再进入具体接口实现
2. Go 内部可演进实现细节，但不得随意破坏跨服务契约
3. Python 端的 Pydantic schema、Mock Gateway、contract tests 必须与本文保持一致
4. 发生契约变更时，必须同步：
   - `references/api-event-contracts.md`
   - `references/python-service-api.md`
   - `references/database-design.md`
   - `references/implementation-plan.md`
   - `references/change-log.md`

## 15. 当前状态结论

- 当前版本为 **v1 正式草案**
- 已覆盖：边界、records API、query DSL、metadata、事件 envelope、执行启动、审批恢复、错误码、Mock 方案
- 后续仍需细化的实现级内容：
  - records query 过滤 DSL 的最终字段约束
  - 事件传输层的具体 Redis/桥接实现
  - 更细的 approval 状态机
  - contract tests 的自动化校验清单
