# Python 智能体协同服务代码结构

## 1. 目标
本目录结构用于支撑以下能力：
- FastAPI 对外服务
- LangGraph 工作流执行器
- workflow 定义 / 版本 / 发布管理
- 对话入口、审批恢复、监控查询
- 三级记忆与工具调用扩展

## 2. 推荐目录树
```text
python-agent-service/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  ├─ security.py
│  │  ├─ errors.py
│  │  └─ deps.py
│  ├─ api/
│  │  ├─ router.py
│  │  └─ v1/
│  │     ├─ workflows.py
│  │     ├─ executions.py
│  │     ├─ chat.py
│  │     ├─ monitor.py
│  │     └─ approvals.py
│  ├─ schemas/
│  │  ├─ workflow.py
│  │  ├─ execution.py
│  │  ├─ event.py
│  │  ├─ chat.py
│  │  ├─ approval.py
│  │  └─ monitor.py
│  ├─ domain/
│  │  ├─ workflows/
│  │  │  ├─ models.py
│  │  │  ├─ service.py
│  │  │  ├─ compiler.py
│  │  │  └─ repository.py
│  │  ├─ executions/
│  │  │  ├─ models.py
│  │  │  ├─ service.py
│  │  │  ├─ state_store.py
│  │  │  └─ repository.py
│  │  ├─ approvals/
│  │  │  ├─ models.py
│  │  │  ├─ service.py
│  │  │  └─ repository.py
│  │  ├─ chat/
│  │  │  ├─ models.py
│  │  │  ├─ service.py
│  │  │  └─ repository.py
│  │  ├─ monitor/
│  │  │  ├─ service.py
│  │  │  └─ repository.py
│  │  └─ memory/
│  │     ├─ context.py
│  │     ├─ history.py
│  │     ├─ knowledge.py
│  │     └─ service.py
│  ├─ runtime/
│  │  ├─ graph_builder.py
│  │  ├─ dispatcher.py
│  │  ├─ handlers/
│  │  │  ├─ sensor.py
│  │  │  ├─ decision.py
│  │  │  ├─ execution.py
│  │  │  ├─ dialog.py
│  │  │  ├─ condition.py
│  │  │  ├─ parallel.py
│  │  │  ├─ loop.py
│  │  │  ├─ subflow.py
│  │  │  ├─ wait.py
│  │  │  ├─ approval.py
│  │  │  └─ exception.py
│  │  ├─ checkpoints/
│  │  │  ├─ base.py
│  │  │  └─ postgres.py
│  │  └─ events/
│  │     ├─ consumer.py
│  │     ├─ publisher.py
│  │     └─ sse.py
│  ├─ integrations/
│  │  ├─ go_client/
│  │  │  ├─ records.py
│  │  │  ├─ approvals.py
│  │  │  └─ auth.py
│  │  ├─ tools/
│  │  │  ├─ registry.py
│  │  │  └─ executors/
│  │  ├─ llm/
│  │  │  ├─ client.py
│  │  │  ├─ prompts.py
│  │  │  └─ embeddings.py
│  │  └─ rag/
│  │     ├─ index.py
│  │     ├─ retriever.py
│  │     └─ loader.py
│  ├─ db/
│  │  ├─ base.py
│  │  ├─ session.py
│  │  ├─ models/
│  │  │  ├─ workflow.py
│  │  │  ├─ execution.py
│  │  │  ├─ approval.py
│  │  │  ├─ memory.py
│  │  │  └─ audit.py
│  │  └─ migrations/
│  └─ tests/
│     ├─ unit/
│     ├─ integration/
│     └─ contract/
├─ scripts/
├─ docs/
└─ pyproject.toml
```

## 3. 模块职责说明

### 3.1 `app/main.py`
- FastAPI 应用入口
- 注册路由、中间件、异常处理、生命周期事件

### 3.2 `app/core/`
- 配置加载、日志、鉴权依赖、统一错误码
- 与业务无关的通用基础设施

### 3.3 `app/api/`
- 只负责 HTTP 层
- 参数校验、调用 service、返回 response model
- 不直接写业务编排逻辑

### 3.4 `app/schemas/`
- Pydantic 请求/响应模型
- 对应 Workflow / Execution / Chat / Event / Approval / Monitor 契约

### 3.5 `app/domain/`
- 业务领域层
- 负责 workflow/service/repository 分层
- 每个子域各管自己的数据与规则

### 3.6 `app/runtime/`
- 真正的 LangGraph 执行时核心
- `graph_builder.py`：从 execution_dag 构建图
- `dispatcher.py`：路由节点到 handler
- `handlers/`：每种节点一个 handler 文件
- `checkpoints/`：checkpoint 适配层
- `events/`：事件消费与状态推送

说明：
- `monitor/` 领域和监控工作台 API 仍存在
- 但监控型智能体本体不应作为普通 runtime handler 实现
- 监控型智能体应以后续控制平面服务方式落地

### 3.7 `app/integrations/`
- 所有外部依赖适配器
- 包括 Go API、工具系统、LLM、RAG、嵌入模型
- 防止外部调用散落在业务域中

### 3.8 `app/db/`
- ORM 模型、session、迁移
- 与 domain.repository 配合

### 3.9 `app/tests/`
- `unit/`：纯逻辑测试
- `integration/`：服务集成测试
- `contract/`：Go ↔ Python / 前端 ↔ Python 契约测试

## 4. 与当前设计文档的映射

### 4.1 workflow-dsl.md
- 落位到：
  - `app/schemas/workflow.py`
  - `app/domain/workflows/compiler.py`
  - `app/runtime/graph_builder.py`

### 4.2 workflow-publish-state-machine.md
- 落位到：
  - `app/domain/workflows/service.py`
  - `app/db/models/workflow.py`

### 4.3 api-event-contracts.md
- 落位到：
  - `app/schemas/event.py`
  - `app/api/v1/*.py`
  - `app/runtime/events/consumer.py`
  - `app/runtime/events/publisher.py`

### 4.4 langgraph-runtime.md
- 落位到：
  - `app/runtime/`
  - `app/domain/executions/`

### 4.5 memory-model.md
- 落位到：
  - `app/domain/memory/`
  - `app/integrations/rag/`
  - `app/db/models/memory.py`

## 5. 开发边界建议
- API 层不允许直接操作数据库模型
- handler 不直接发 HTTP 响应，只返回节点输出
- Go 相关调用统一走 `integrations/go_client/`
- 所有审批恢复逻辑统一走 `domain/approvals/service.py`
- 所有执行状态变更统一走 `domain/executions/service.py`

## 6. 第一阶段最小落地顺序
1. `core/` + `main.py`
2. `schemas/workflow.py` + `schemas/execution.py`
3. `db/models/workflow.py` + `db/models/execution.py`
4. `domain/workflows/` + `domain/executions/`
5. `runtime/graph_builder.py` + `runtime/dispatcher.py`
6. `runtime/handlers/sensor.py` / `decision.py` / `execution.py` / `approval.py`
7. `api/v1/workflows.py` + `api/v1/executions.py`
8. `runtime/events/consumer.py` + `events/publisher.py`

监控型智能体不纳入第一阶段 runtime handler 列表，后续按独立监控子系统实现。

## 7. 后续扩展位点
- 增加更多工具执行器：`integrations/tools/executors/`
- 增加更多知识检索适配器：`integrations/rag/`
- 增加更多节点类型：`runtime/handlers/`
- 增加前端实时推送通道：`runtime/events/sse.py`
