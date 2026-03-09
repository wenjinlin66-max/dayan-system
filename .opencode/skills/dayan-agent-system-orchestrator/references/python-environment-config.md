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
DEFAULT_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=<YOUR_DEEPSEEK_API_KEY>
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
```

## 4. 配置解释

### 4.1 PostgreSQL
- 当前连接的是 Docker 版 PostgreSQL + pgvector
- 不是本机未装扩展的 PostgreSQL 实例

### 4.2 Redis
- 当前连接的是 Docker 版 Redis
- 默认无密码

### 4.3 MinIO
- 当前连接的是 Docker 版 MinIO
- 用于 PDF、语音、OCR 中间文件、文档上传

### 4.4 模型
- 默认 LLM：DeepSeek 在线 API
- Embedding / Rerank：当前规划为本地部署
- GPU：当前已确认可用

### 4.5 实时推送
- 第一阶段默认 SSE
- WebSocket 暂不作为默认实现

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

REDIS_HOST=localhost
REDIS_PORT=56379
REDIS_PASSWORD=
REDIS_DB=0

S3_ENDPOINT=http://localhost:59000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dayan-agent-files
S3_REGION=us-east-1

DEFAULT_LLM_PROVIDER=deepseek
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
