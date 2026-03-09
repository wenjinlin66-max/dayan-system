# 数据库设计模板

## 1. 设计原则
- Python 不直连 Go 业务数据库
- 权限隔离字段必须显式设计
- 关键审计数据必须可追溯

## 2. 核心实体清单
| 实体 | 说明 | 所属层 | 备注 |
|---|---|---|---|
| workflows | 工作流定义主表 | AI 中枢 | Python 真相源 |
| workflow_versions | 工作流版本表 | AI 中枢 | 包含 draft/released |
| workflow_node_configs | 节点配置快照 | AI 中枢 | 可选，供拆分存储 |
| agent_configs | 智能体配置 | AI 中枢 | |
| execution_runs | 流程执行实例 | AI 中枢 | |
| execution_checkpoints | 执行 checkpoint 索引 | AI 中枢 | 对接 LangGraph |
| approval_tasks | 审批运行态镜像 | AI 中枢 | 非审批主记录 |
| audit_logs | 审计日志 | AI 中枢 | |
| agent_memories | 历史执行记忆 | AI 中枢 | |
| rag_docs_index | 知识索引元数据 | AI 中枢 | |
| chat_sessions | 对话工作台会话 | AI 中枢 | |
| chat_messages | 对话消息 | AI 中枢 | |
| tool_run_logs | 工具执行轨迹 | AI 中枢 | |
| monitor_snapshots | 监控快照 | AI 中枢 | |

## 2.1 工作流版本原则
- Python 数据库持有 workflow definitions 与 execution_dag
- `ui_schema` 与 `execution_dag` 必须分字段或分表存储
- 发布动作由 Python 完成，发布后生成不可变版本快照
- 草稿版仅用于编辑或沙盒测试，正式执行默认只读取 released 版本

## 2.2 推荐关键表

### workflows
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 工作流主键 |
| code | varchar(128) | 是 |  | unique | 工作流编码 |
| name | varchar(255) | 是 |  |  | 工作流名称 |
| owner_dept_id | varchar(64) | 是 |  | index | 所属部门 |
| visibility | varchar(32) | 是 | private |  | 可见性 |
| latest_draft_version | int | 否 | null |  | 最新草稿版本号 |
| current_release_version | int | 否 | null |  | 当前发布版本号 |
| status | varchar(32) | 是 | active | index | active/archived |
| created_by | varchar(64) | 是 |  |  | 创建人 |
| updated_by | varchar(64) | 是 |  |  | 更新人 |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### workflow_versions
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 版本主键 |
| workflow_id | uuid | 是 |  | unique(workflow_id, version) | 归属 workflow |
| version | int | 是 |  | unique(workflow_id, version) | 版本号 |
| mode | varchar(32) | 是 | draft | index | draft/released/sandbox |
| ui_schema | jsonb | 是 |  |  | 画布编辑态 |
| execution_dag | jsonb | 否 | null |  | 编译后的执行态 |
| compile_status | varchar(32) | 是 | pending |  | pending/success/failed |
| compile_errors | jsonb | 否 | null |  | 编译错误 |
| schema_version | varchar(32) | 是 |  |  | DSL schema 版本 |
| content_hash | varchar(128) | 否 | null | index | 执行 DAG 指纹 |
| release_note | text | 否 | null |  | 发布说明 |
| is_current_release | boolean | 是 | false | index | 是否当前发布版 |
| created_by | varchar(64) | 是 |  |  | 创建人 |
| created_at | timestamptz | 是 | now() |  | |
| released_at | timestamptz | 否 | null |  | 发布时间 |

### execution_runs
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | execution_id |
| workflow_id | uuid | 是 |  | index | |
| workflow_version | int | 是 |  |  | 执行版本 |
| mode | varchar(32) | 是 | released |  | released/sandbox |
| thread_id | varchar(128) | 是 |  | unique | LangGraph thread_id |
| entry_node | varchar(128) | 是 |  |  | 入口节点 |
| current_node | varchar(128) | 否 | null |  | 当前节点 |
| status | varchar(32) | 是 | pending | index | pending/running/waiting_approval/succeeded/failed/cancelled |
| trigger_type | varchar(64) | 是 |  |  | event/chat/manual/schedule |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| started_by | varchar(64) | 否 | null |  | 发起人 |
| trigger_event_id | varchar(128) | 否 | null | index | 触发事件 ID |
| correlation_id | varchar(128) | 否 | null | index | 跨服务关联 ID |
| context_snapshot | jsonb | 否 | null |  | 当前上下文快照 |
| final_output | jsonb | 否 | null |  | 最终执行结果 |
| error_summary | text | 否 | null |  | 失败摘要 |
| started_at | timestamptz | 否 | null |  | |
| finished_at | timestamptz | 否 | null |  | |

### execution_checkpoints
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | checkpoint 主键 |
| execution_id | uuid | 是 |  | index | 对应 execution |
| thread_id | varchar(128) | 是 |  | index | LangGraph thread_id |
| checkpoint_key | varchar(255) | 是 |  | unique | checkpoint 唯一键 |
| checkpoint_data | jsonb | 是 |  |  | 持久化状态 |
| current_node | varchar(128) | 否 | null |  | checkpoint 对应节点 |
| created_at | timestamptz | 是 | now() |  | |

### approval_tasks
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | Python 运行态镜像主键 |
| go_approval_id | varchar(128) | 是 |  | unique | Go 审批主记录 ID |
| execution_id | uuid | 是 |  | index | 对应执行实例 |
| node_id | varchar(128) | 是 |  |  | 审批节点 |
| status | varchar(32) | 是 | pending | index | pending/approved/rejected/resumed |
| dept_id | varchar(64) | 是 |  | index | |
| snapshot | jsonb | 是 |  |  | 审批时上下文快照 |
| resume_payload | jsonb | 否 | null |  | 恢复输入 |
| decided_by | varchar(64) | 否 | null |  | 审批操作人 |
| decided_at | timestamptz | 否 | null |  | 审批完成时间 |
| created_at | timestamptz | 是 | now() |  | |

### agent_configs
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 配置主键 |
| workflow_id | uuid | 否 | null | index | 归属工作流 |
| node_id | varchar(128) | 否 | null | index | 归属节点 |
| agent_type | varchar(32) | 是 |  | index | sensor/decision/execution/dialog/monitor |
| config | jsonb | 是 |  |  | 节点配置 |
| version | int | 是 | 1 |  | 配置版本 |
| status | varchar(32) | 是 | active | index | active/inactive |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### agent_memories
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 记忆主键 |
| memory_type | varchar(32) | 是 | execution_history | index | execution_history/knowledge_ref |
| agent_type | varchar(32) | 是 |  | index | |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| workflow_id | uuid | 否 | null | index | |
| execution_id | uuid | 否 | null | index | |
| summary | text | 是 |  |  | 摘要 |
| payload | jsonb | 是 |  |  | 结构化内容 |
| tags | jsonb | 否 | null |  | 标签数组 |
| created_at | timestamptz | 是 | now() |  | |

### rag_docs_index
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 文档主键 |
| dept_id | varchar(64) | 是 |  | index | 部门范围 |
| doc_type | varchar(64) | 是 |  | index | pdf/docx/faq/sop |
| title | varchar(255) | 是 |  |  | 标题 |
| source_uri | text | 是 |  |  | 来源 |
| chunk_count | int | 是 | 0 |  | 切片数量 |
| status | varchar(32) | 是 | active | index | active/archived |
| metadata | jsonb | 否 | null |  | 元数据 |
| created_at | timestamptz | 是 | now() |  | |

### chat_sessions
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 会话主键 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| user_id | varchar(64) | 是 |  | index | 用户 |
| title | varchar(255) | 否 | null |  | 会话标题 |
| status | varchar(32) | 是 | active | index | active/closed |
| last_message_at | timestamptz | 否 | null | index | 最近消息时间 |
| created_at | timestamptz | 是 | now() |  | |

### chat_messages
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 消息主键 |
| session_id | uuid | 是 |  | index | 所属会话 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| role | varchar(32) | 是 |  |  | user/assistant/system |
| message_type | varchar(32) | 是 | text |  | text/voice/pdf/card |
| content | text | 否 | null |  | 文本内容 |
| payload | jsonb | 否 | null |  | 多模态内容或卡片 |
| related_execution_id | uuid | 否 | null | index | 关联执行 |
| created_at | timestamptz | 是 | now() |  | |

### tool_run_logs
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 工具运行主键 |
| execution_id | uuid | 是 |  | index | 所属 execution |
| node_id | varchar(128) | 是 |  | index | 所属节点 |
| tool_name | varchar(128) | 是 |  | index | 工具名 |
| status | varchar(32) | 是 | pending | index | pending/success/failed |
| request_payload | jsonb | 否 | null |  | 请求体 |
| response_payload | jsonb | 否 | null |  | 响应体 |
| error_message | text | 否 | null |  | 失败信息 |
| started_at | timestamptz | 否 | null |  | |
| finished_at | timestamptz | 否 | null |  | |

### audit_logs
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 审计主键 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| event_type | varchar(128) | 是 |  | index | 审计事件类型 |
| workflow_id | uuid | 否 | null | index | |
| execution_id | uuid | 否 | null | index | |
| actor_id | varchar(64) | 否 | null | index | 操作人 |
| payload | jsonb | 是 |  |  | 审计详情 |
| created_at | timestamptz | 是 | now() | index | |

### monitor_snapshots
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 快照主键 |
| dept_id | varchar(64) | 否 | null | index | 部门口径 |
| metric_type | varchar(64) | 是 |  | index | qps/error_rate/timeout/deadletter |
| metric_value | numeric(18,6) | 是 | 0 |  | 指标值 |
| metric_payload | jsonb | 否 | null |  | 指标详情 |
| captured_at | timestamptz | 是 | now() | index | 采集时间 |

## 3. 表结构模板
### <table_name>
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|

## 4. 关系与约束
- `workflow_versions.workflow_id -> workflows.id`
- `execution_runs.workflow_id -> workflows.id`
- `execution_checkpoints.execution_id -> execution_runs.id`
- `approval_tasks.execution_id -> execution_runs.id`
- `chat_messages.session_id -> chat_sessions.id`
- `tool_run_logs.execution_id -> execution_runs.id`
- `agent_memories.execution_id -> execution_runs.id`（可空）

### 4.1 关键约束
- 同一 workflow 只能有一个 `current_release_version`
- `execution_id` 与 LangGraph `thread_id` 一一对应
- `approval_tasks.go_approval_id` 全局唯一
- 所有跨部门可见数据必须显式受 `dept_id` 过滤

## 5. 隔离字段设计
- dept_id
- tenant_id（如需）

## 5.1 推荐索引
- `workflow_versions (workflow_id, version)`
- `workflow_versions (workflow_id, is_current_release)`
- `execution_runs (workflow_id, workflow_version, status)`
- `execution_runs (dept_id, status, started_at)`
- `approval_tasks (go_approval_id)`
- `chat_messages (session_id, created_at)`
- `audit_logs (event_type, created_at)`
- `monitor_snapshots (metric_type, captured_at)`

## 6. 迁移策略
- 先建基础主表：workflows、workflow_versions、execution_runs、approval_tasks
- 第二批建支撑表：agent_memories、chat_sessions、chat_messages、tool_run_logs、audit_logs、monitor_snapshots
- 所有新增枚举值优先用 varchar + 约束控制，避免过早强绑定数据库 enum
- JSONB 字段优先用于高变结构：ui_schema、execution_dag、payload、snapshot、metadata

## 7. 待确认项
- 
