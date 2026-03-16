# 第三方依赖清单

## 1. 已确认

### 1.1 数据库与向量能力
- PostgreSQL 17
- pgvector

最终方案：
- 向量库仅使用 `pgvector`
- 第一阶段不引入独立向量数据库

用途：
- PostgreSQL 作为 Python 智能体协同模块主数据库
- PostgreSQL 另建独立数据库 `dayan_mock_records` 作为 Mock 业务表联调底座
- pgvector 作为向量检索能力扩展，用于后续 RAG 能力接入

核心选型理由：
- 当前项目规模下，pgvector 足以支撑第一阶段 RAG 检索
- 减少基础设施数量，降低运维与数据同步复杂度

### 1.2 大模型 API
- 当前默认：Gemini 中转站（OpenAI-compatible API）
- 可替换候选：DeepSeek / ChatGPT / 其他兼容模型服务

凭据注入方式：
- 使用环境变量，不在 skill / 代码 / 文档中保存明文密钥
- 推荐变量名：`LLM_API_KEY`
- 推荐变量名：`LLM_BASE_URL`
- 推荐变量名：`LLM_MODEL`
- 推荐变量名：`LLM_REQUEST_PATH=/chat/completions`
- 推荐变量名：`DEFAULT_LLM_PROVIDER=gemini_proxy`

约束：
- 模型层必须做成可替换适配器，不得把业务逻辑写死到单一厂商 SDK
- 决策型/对话型智能体调用模型时，应通过统一 LLM client 层接入
- 当前运行方式：Gemini 通过 OpenAI-compatible 中转站网关接入

当前已验证的 OpenAI-compatible relay 调用口径：
- 中转 base URL：`https://api.laozhang.ai/v1`
- Chat Completions 路径：`/chat/completions`
- Responses 路径：`/responses`
- SDK 形态：`OpenAI(api_key=..., base_url="https://api.laozhang.ai/v1")`
- Dayan 当前默认优先使用 Chat Completions，因此后端环境变量默认应配置：`LLM_REQUEST_PATH=/chat/completions`；若需要切到 OpenAI Responses 口径，直接改为 `LLM_REQUEST_PATH=/responses`

接入示例（文档中不记录真实 key）：

```python
from openai import OpenAI

client = OpenAI(
    api_key="<YOUR_TEST_KEY>",
    base_url="https://api.laozhang.ai/v1",
)

chat_completion = client.chat.completions.create(
    model="gpt-4o-mini",
    stream=False,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)

response = client.responses.create(
    model="gpt-4o-mini",
    input="Hello!",
    instructions="You are a helpful assistant.",
)
```

### 1.3 Python 基础框架
- FastAPI
- LangGraph
- Pydantic
- SQLAlchemy
- Alembic

推荐方案：
- SQLAlchemy 2.0（Async）
- 数据库驱动：asyncpg
- LangGraph：`0.2.x` 稳定线（当前先锁定 `0.2.56`）

用途：
- FastAPI：Python 智能体协同服务 API 层
- LangGraph：工作流执行器与智能体编排运行时
- Pydantic：请求响应模型、DSL schema、配置校验
- SQLAlchemy：ORM 与数据访问层
- Alembic：数据库迁移

核心选型理由：
- SQLAlchemy 2.0 Async 原生支持异步，适配 FastAPI
- asyncpg 对 PostgreSQL 17 适配成熟，性能优于同步驱动路线

### 1.4 检索增强
- 需要 Embedding 模型
- 需要 Rerank 模型

推荐方案：
- Embedding 模型：BGE-M3（本地）
- Rerank 模型：BGE Reranker v2-m3

约束：
- Embedding 与 Rerank 需要通过可替换适配器接入
- 第一阶段允许先占位，不强制立即定死具体厂商

核心选型理由：
- 中文语义能力强，多语言兼容较好
- 适合本地部署，便于数据私有化
- 与 pgvector 检索链路兼容性高

当前运行方式：
- Embedding：本地部署
- Rerank：本地部署
- GPU：有

### 1.5 消息队列与实时通信
- Redis
- Asynq
- SSE
- WebSocket
- 需要任务调度器

推荐方案：
- 调度方案：APScheduler + Redis

说明：
- Redis + Asynq：事件总线与异步任务基础
- SSE：默认前端执行状态推送方案
- WebSocket：作为后续增强或复杂交互候选
- 调度器：用于定时巡检、定时触发感知型智能体

核心选型理由：
- APScheduler 轻量，适合 Python 进程内定时任务
- Redis 可配合任务状态、分布式锁和调度协调

当前状态：
- Redis：已通过 Docker 搭建（容器 `dayan-redis`）

最终方案：
- Redis 部署方式：Docker 单实例（当前阶段）
- 实时推送默认：SSE
- WebSocket：后续仅在复杂双向交互场景再引入

### 1.6 文件与多模态
- PDF 解析
- 语音转文字
- 图片 OCR
- Office 文档处理

推荐方案：
- PDF：PyMuPDF
- OCR：PaddleOCR
- 语音转文字：Whisper

核心选型理由：
- PyMuPDF 速度快，适合 PDF 文本抽取
- PaddleOCR 中文识别稳定
- Whisper 适合语音转文字主链

### 1.7 前端补充依赖
- Axios
- ECharts
- 图标库（待定具体方案）
- 上传组件（待定具体方案）

最终方案：
- 图标库：Iconify（推荐配合 `@iconify/vue`）
- 上传组件：Element Plus Upload

核心选型理由：
- Iconify 图标覆盖广，便于后续统一风格
- Element Plus Upload 与当前前端主栈一致，减少额外依赖

### 1.8 部署与运维
- Docker
- Nginx
- 监控平台（待定具体方案）
- 错误追踪（待定具体方案）
- 对象存储（待定具体方案）

推荐方案：
- 监控（APM）：Prometheus + Grafana
- 错误追踪：Sentry（自建版）
- 对象存储：MinIO

核心选型理由：
- Prometheus + Grafana 适合 Agent 执行指标与运行监控
- Sentry 适合 Python/前端统一错误追踪
- MinIO 与 Docker 集成友好，API 兼容 S3

当前状态：
- 对象存储：已通过 Docker 搭建 MinIO（bucket: `dayan-agent-files`）

### 1.9 MCP / 工具调用
最终方案：
- 采用“工具注册表 + 适配器”模式
- MCP 工具作为一类 adapter 接入
- 第三方 API、Go 泛型 API、文件处理能力统一抽象为 tool executors
- 部门表格写入能力统一抽象为 `department_table` 执行目标，并通过 tool executor / adapter 路线接入具体表格载体

推荐实现：
- `tool registry` 统一注册
- `executors/` 按工具类别拆分
- workflow / execution_agent 只依赖统一工具接口，不直接耦合具体 SDK

当前实现推进：
- `ToolRegistry.build_default()` 已落地为当前默认入口
- `department_table` 当前通过 `DepartmentTableExecutor` 接入
- adapter 支持两条路径：Go `records API` / `MockRecordsGateway`
- 对于前端真实业务表格联调，当前再增加一条独立底座：`dayan_mock_records` + Python Mock Records API

核心选型理由：
- 方便后续扩展飞书、邮件、审批、文件处理等能力
- 方便按部门路由到不同表格资源，同时避免在 execution_agent 中写死某个表格厂商
- 降低 execution_agent 与外部服务的耦合

### 1.10 Office 文档处理
最终方案：
- Word：python-docx
- Excel：openpyxl
- Office 转换/预处理：LibreOffice（命令行）

核心选型理由：
- python-docx / openpyxl 是 Python 生态成熟方案
- LibreOffice 适合处理格式转换和批量文档预处理

## 2. 已知项目技术栈（非插件但需统一记录）

### 2.1 前端
- Vue 3
- Element Plus
- Tailwind CSS
- VTable
- Vue Flow
- form-create

### 2.2 Go 侧基础
- Gin
- PostgreSQL + GORM（企业租户主数据）
- 元数据 + JSONB 动态数据层
- golang-migrate
- expr（动态条件评估）
- Asynq / Redis
- jsonschema
- goqu
- gjson / sjson

## 3. 待确认
- MCP / 工具调用插件清单（具体首批工具）

### 3.1 MCP 当前状态
- MCP 能力保留接口预留
- 首批具体插件清单暂未确定
- 当前开发阶段先按“工具注册表 + adapter”模式预留扩展位

## 4. 记录规则
- 每新增一个第三方依赖，都要记录：名称、用途、所属层、是否可替换、当前状态
- 若某依赖可替换，必须记录候选替代项
- 若某依赖影响接口契约或数据库结构，必须同步更新其他设计文档
