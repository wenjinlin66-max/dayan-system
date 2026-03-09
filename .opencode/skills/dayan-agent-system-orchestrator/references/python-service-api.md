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
- `PUT /api/v1/workflows/:workflow_id/draft`
- `POST /api/v1/workflows/:workflow_id/compile`
- `POST /api/v1/workflows/:workflow_id/publish`
- `GET /api/v1/workflows/:workflow_id/releases/current`
- `GET /api/v1/workflows/:workflow_id/releases/:version`

### 2.2 Execution API
- `POST /api/v1/executions/start`
- `GET /api/v1/executions/:execution_id`
- `GET /api/v1/executions/:execution_id/timeline`
- `POST /api/v1/executions/:execution_id/resume`
- `POST /api/v1/executions/:execution_id/cancel`

### 2.3 Chat API
- `POST /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions/:session_id/messages`
- `GET /api/v1/chat/sessions/:session_id/messages`
- `GET /api/v1/chat/sessions/:session_id/approvals`

### 2.4 Monitor API
- `GET /api/v1/monitor/executions`
- `GET /api/v1/monitor/metrics`
- `GET /api/v1/monitor/deadletters`

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
