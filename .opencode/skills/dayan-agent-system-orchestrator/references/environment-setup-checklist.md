# 环境与外部资源准备清单

## 1. 必做项（立即准备）

### 1.1 PostgreSQL 17 + pgvector
你需要完成：
- 在 pgAdmin 中创建一个供 Python 智能体协同模块使用的数据库
- 数据库建议名：`dayan_agentic`
- 确认 PostgreSQL 版本为 17
- 在目标数据库中启用 `vector` 扩展（pgvector）

建议你准备并记录：
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE=dayan_agentic`

### 1.2 Redis
你需要完成：
- 准备一个 Redis 实例
- 确认 Python 与 Go 都能访问
- 记录连接信息：
  - `REDIS_HOST`
  - `REDIS_PORT`
  - `REDIS_PASSWORD`（如有）
  - `REDIS_DB`

### 1.3 DeepSeek API
你需要完成：
- 保留你的 DeepSeek API Key
- 不写入 skill 文档，改为本地环境变量

建议变量：
- `DEEPSEEK_API_KEY`
- `DEFAULT_LLM_PROVIDER=deepseek`

### 1.4 MinIO / 对象存储
你需要完成：
- 准备一个 MinIO 实例或等效对象存储
- 至少准备一个 bucket，用于：
  - PDF / 文档上传
  - 语音文件
  - OCR 中间文件

建议变量：
- `S3_ENDPOINT`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `S3_REGION`

## 2. 建议尽快确认

### 2.1 数据库驱动与连接方式
当前推荐：
- SQLAlchemy 2.0 Async
- asyncpg

你需要确认：
- 是否接受 async 路线作为唯一标准

### 2.2 LangGraph 版本
当前默认方案：
- LangGraph 锁定 `0.2.56`

说明：
- 先使用 0.2 稳定线，避免过早追最新版本带来接口波动

### 2.3 Embedding / Rerank
当前推荐：
- BGE-M3
- BGE Reranker v2-m3

你需要确认：
- 本地部署还是远程推理
- 部署机器是否有 GPU

### 2.4 实时推送方案
当前建议：
- 默认 SSE
- WebSocket 作为增强方案

你需要确认：
- 第一阶段是否只用 SSE（当前默认方案：是）

### 2.5 向量检索方案
当前默认方案：
- 仅使用 pgvector
- 第一阶段不引入独立向量数据库

### 2.6 Office 处理方案
当前默认方案：
- Word：python-docx
- Excel：openpyxl
- 转换/预处理：LibreOffice

## 3. 你现在可以立刻去做的操作

### 操作 A：在 pgAdmin 创建数据库
1. 打开 pgAdmin
2. 连接你的 PostgreSQL 17 实例
3. 新建数据库：`dayan_agentic`（当前实际环境已创建为 `dayan_agentic2`）
4. 在 query tool 执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

5. 把以下结果告诉我：
- 数据库名
- 用户名
- host
- port
- 是否成功启用 vector 扩展

### 当前已知环境状态
- 数据库名：`dayan_agentic2`
- owner：`postgres`
- 数据库创建：成功
- `CREATE EXTENSION vector`：失败
- 当前报错：`extension "vector" is not available`

### 对该报错的解释
这说明 PostgreSQL 实例当前没有安装 pgvector 扩展文件，
不是 SQL 语法问题，也不是数据库名问题。

Windows 下通常表示：
- `vector.control` 文件不存在于 PostgreSQL 的 extension 目录
- 或者 pgvector 尚未安装到当前 PostgreSQL 17 实例

### 当前已落地的可用替代方案（已执行）
- 方案：Docker PostgreSQL 17 + pgvector
- 容器名：`dayan-pgvector`
- 数据库名：`dayan_agentic2`
- 用户名：`postgres`
- 密码：`postgres`
- Host：`localhost`
- Port：`55432`
- `CREATE EXTENSION IF NOT EXISTS vector;`：成功
- 当前扩展列表：`plpgsql`, `vector`

对应 docker compose 文件：
- `infra/pgvector/docker-compose.yml`

### 操作 B：确认 Redis
把以下信息告诉我：
- Redis 是否已安装/可用
- host
- port
- 是否需要密码

当前探测结果：
- 已创建 Docker Redis 容器：`dayan-redis`
- Host：`localhost`
- Port：`56379`
- 密码：无
- `redis-cli ping`：`PONG`
- 当前判断：Redis 已可用

### 操作 C：确认对象存储
把以下信息告诉我：
- 用 MinIO 还是其他对象存储
- endpoint
- bucket 名称是否已创建

当前已确认：
- 对象存储：已通过 Docker 搭建 MinIO
- 容器名：`dayan-minio`
- API Endpoint：`http://localhost:59000`
- Console：`http://localhost:59001`
- Bucket：`dayan-agent-files`
- Access Key：`minioadmin`
- Secret Key：`minioadmin`
- Bucket 创建结果：成功

### 操作 D：确认模型推理方式
把以下信息告诉我：
- DeepSeek 先走在线 API 还是本地代理（当前已确认：在线 API）
- BGE-M3 / Rerank 是否准备本地部署（当前已确认：本地）
- 机器是否有 GPU（当前已确认：有）

## 4. 返回给我的最小信息模板
你完成后直接按下面回我：

```text
PostgreSQL:
- host:
- port:
- user:
- database:
- vector扩展是否成功:

Redis:
- host:
- port:
- password:

对象存储:
- 方案:
- endpoint:
- bucket:

模型:
- DeepSeek: 在线API/本地代理
- Embedding: 本地/远程
- Rerank: 本地/远程
- GPU: 有/无
```

## 5. 当前推荐连接信息（Python 模块）
建议 Python 模块优先连接 Docker 版 pgvector 数据库，而不是本机未装扩展的 PostgreSQL：

```text
PGHOST=localhost
PGPORT=55432
PGUSER=postgres
PGPASSWORD=postgres
PGDATABASE=dayan_agentic2
```

Redis 推荐连接信息：

```text
REDIS_HOST=localhost
REDIS_PORT=56379
REDIS_PASSWORD=
REDIS_DB=0
```

对象存储推荐连接信息：

```text
S3_ENDPOINT=http://localhost:59000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dayan-agent-files
S3_REGION=us-east-1
```
