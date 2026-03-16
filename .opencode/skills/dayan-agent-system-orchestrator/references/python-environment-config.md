# Python 项目环境变量与配置文档

## 1. 目标
本文件用于统一管理 Python 智能体协同服务在本地开发、测试环境中的配置来源。

原则：
- 所有敏感信息通过环境变量注入
- 业务代码不直接写死连接信息
- 本地开发优先使用已落地的 Docker 资源

## 2. 推荐配置分层

### 2.1 基础配置
- `APP_NAME`
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `LOG_LEVEL`

### 2.2 数据库配置
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE`
- `MOCK_PGHOST`
- `MOCK_PGPORT`
- `MOCK_PGUSER`
- `MOCK_PGPASSWORD`
- `MOCK_PGDATABASE`

### 2.3 Redis 配置
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `REDIS_DB`

### 2.4 对象存储配置
- `S3_ENDPOINT`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `S3_REGION`

### 2.5 模型与检索配置
- `DEFAULT_LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_REQUEST_PATH`
- `LLM_TIMEOUT_MS`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `RERANK_PROVIDER`
- `RERANK_MODEL`
- `USE_GPU`

### 2.6 运行时配置
- `LANGGRAPH_VERSION_PIN`
- `REALTIME_TRANSPORT`
- `WORKFLOW_DEFAULT_MODE`
- `ENABLE_SANDBOX_MODE`
- `SCHEDULER_ENABLED`
- `GO_RECORDS_BASE_URL`
- `GO_RECORDS_TIMEOUT_MS`
- `RUNTIME_DEFAULT_TENANT_ID`
- `ENABLE_MOCK_RECORDS_GATEWAY`
- `DEPARTMENT_TABLE_ROUTE_MAP_JSON`

## 3. 当前推荐环境变量

```text
# =========================
# App
# =========================
APP_NAME=dayan-agent-service
APP_ENV=local
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# =========================
# PostgreSQL + pgvector
# =========================
PGHOST=localhost
PGPORT=55432
PGUSER=postgres
PGPASSWORD=postgres
PGDATABASE=dayan_agentic2

MOCK_PGHOST=localhost
MOCK_PGPORT=55432
MOCK_PGUSER=postgres
MOCK_PGPASSWORD=postgres
MOCK_PGDATABASE=dayan_mock_records

# =========================
# Redis
# =========================
REDIS_HOST=localhost
REDIS_PORT=56379
REDIS_PASSWORD=
REDIS_DB=0

# =========================
# MinIO / S3 Compatible Storage
# =========================
S3_ENDPOINT=http://localhost:59000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dayan-agent-files
S3_REGION=us-east-1

# =========================
# LLM / Embedding / Rerank
# =========================
DEFAULT_LLM_PROVIDER=gemini_proxy
LLM_API_KEY=<YOUR_PROXY_API_KEY>
LLM_BASE_URL=https://<your-proxy-host>/v1
LLM_MODEL=gemini-3-flash-preview-thinking
LLM_REQUEST_PATH=/chat/completions
LLM_TIMEOUT_MS=30000

DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BGE-M3

RERANK_PROVIDER=local
RERANK_MODEL=BGE-Reranker-v2-m3

USE_GPU=true

# =========================
# Runtime
# =========================
LANGGRAPH_VERSION_PIN=0.2.56
REALTIME_TRANSPORT=sse
WORKFLOW_DEFAULT_MODE=released
ENABLE_SANDBOX_MODE=true
SCHEDULER_ENABLED=true
GO_RECORDS_BASE_URL=
GO_RECORDS_TIMEOUT_MS=8000
RUNTIME_DEFAULT_TENANT_ID=tenant_local
ENABLE_MOCK_RECORDS_GATEWAY=true
DEPARTMENT_TABLE_ROUTE_MAP_JSON={}
```

## 4. 配置解释

### 4.1 PostgreSQL
- 当前连接的是 Docker 版 PostgreSQL + pgvector
- 不是本机未装扩展的 PostgreSQL 实例
- 主库 `dayan_agentic2` 与 Mock 业务库 `dayan_mock_records` 必须逻辑分离
- Mock 业务库只服务于业务表格联调与感知型智能体事件触发，不承载 workflow/chat/approval 主真相数据
- Go 正式 records 能力接入后，`MOCK_PG*` 配置允许整体删除
- 当前实现中，服务启动会尝试自动创建 `dayan_mock_records`；若 PostgreSQL 账号没有 `CREATE DATABASE` 权限，则需提前手工创建该库

### 4.2 Redis
- 当前连接的是 Docker 版 Redis
- 默认无密码

### 4.3 MinIO
- 当前连接的是 Docker 版 MinIO
- 用于 PDF、语音、OCR 中间文件、文档上传

### 4.4 模型
- 默认 LLM：Gemini 中转站（OpenAI-compatible）
- Embedding / Rerank：当前规划为本地部署
- GPU：当前已确认可用
- 推荐优先使用 OpenAI Chat compatible 接法：`base_url=/v1` + `/chat/completions`
- 当前代码已同时兼容 `LLM_REQUEST_PATH=/chat/completions` 与 `LLM_REQUEST_PATH=/responses`；若中转站需要 OpenAI Responses 口径，可直接切换该变量，无需再改业务调用层
- 禁止把真实 API key 写入 `.env.example`、skill 文档、代码常量或提交记录
- 当前代码已支持在 Python 服务根目录自动读取 `.env.local` 与 `.env`，且仅在进程环境未显式注入时回填；本地调试时优先使用 `.env.local`
- 若历史环境仍使用 `GEMINI_PROXY_API_KEY / GEMINI_PROXY_BASE_URL` 命名，当前代码也已兼容回退到这组变量，避免 Gemini 中转站已配置但 ChatWorkbench 仍误报 `LLM_NOT_CONFIGURED`
- 前端本地联调若需绕开默认 `8000` 端口残留监听，可通过 `VITE_API_TARGET=http://127.0.0.1:8001` 等方式切换 Vite 代理目标到干净后端实例

### 4.5 实时推送
- 第一阶段默认 SSE
- WebSocket 暂不作为默认实现

### 4.6 Go Records / department_table adapter
- `GO_RECORDS_BASE_URL`：Go 泛型 records API 的基础地址
- `GO_RECORDS_TIMEOUT_MS`：Python 调用 Go records API 的超时时间
- `RUNTIME_DEFAULT_TENANT_ID`：当前 runtime 侧默认 tenant_id
- `ENABLE_MOCK_RECORDS_GATEWAY`：当 Go records API 未配置时，是否允许退回 mock adapter
- `DEPARTMENT_TABLE_ROUTE_MAP_JSON`：`target_ref -> table_id/provider/dept_id` 的 JSON 路由表

推荐示例：
```json
{
  "dept_table.production.replenishment_register": {
    "table_id": "replenishment_requests",
    "provider": "bitable",
    "dept_id": "production"
  }
}
```

## 5. 建议的 `.env.local` 模板

```text
APP_NAME=dayan-agent-service
APP_ENV=local
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

PGHOST=localhost
PGPORT=55432
PGUSER=postgres
PGPASSWORD=postgres
PGDATABASE=dayan_agentic2

MOCK_PGHOST=localhost
MOCK_PGPORT=55432
MOCK_PGUSER=postgres
MOCK_PGPASSWORD=postgres
MOCK_PGDATABASE=dayan_mock_records

REDIS_HOST=localhost
REDIS_PORT=56379
REDIS_PASSWORD=
REDIS_DB=0

S3_ENDPOINT=http://localhost:59000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dayan-agent-files
S3_REGION=us-east-1

DEFAULT_LLM_PROVIDER=gemini_proxy
LLM_API_KEY=
LLM_BASE_URL=https://<your-proxy-host>/v1
LLM_MODEL=gemini-3-flash-preview-thinking
LLM_REQUEST_PATH=/chat/completions
LLM_TIMEOUT_MS=30000

DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BGE-M3

RERANK_PROVIDER=local
RERANK_MODEL=BGE-Reranker-v2-m3

USE_GPU=true

LANGGRAPH_VERSION_PIN=0.2.56
REALTIME_TRANSPORT=sse
WORKFLOW_DEFAULT_MODE=released
ENABLE_SANDBOX_MODE=true
SCHEDULER_ENABLED=true
GO_RECORDS_BASE_URL=
GO_RECORDS_TIMEOUT_MS=8000
RUNTIME_DEFAULT_TENANT_ID=tenant_local
ENABLE_MOCK_RECORDS_GATEWAY=true
DEPARTMENT_TABLE_ROUTE_MAP_JSON={}
```

## 6. Python 配置模块建议
建议在 `app/core/config.py` 中统一读取上述变量，并导出强类型配置对象。

推荐分组：
- `AppSettings`
- `DatabaseSettings`
- `RedisSettings`
- `StorageSettings`
- `LLMSettings`
- `RuntimeSettings`

## 7. 当前阶段注意事项
- `DEEPSEEK_API_KEY` 只放本地环境变量，不写入仓库
- PostgreSQL / Redis / MinIO 都已经有本地 Docker 版可用实例
- 若后续迁移到测试环境，只需替换连接变量，不改业务代码
