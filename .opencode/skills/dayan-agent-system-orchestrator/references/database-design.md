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
| sensor_subscriptions | 感知订阅配置 | AI 中枢 | 第一阶段重点 |
| sensor_event_inbox | 感知事件入箱 | AI 中枢 | 第一阶段重点 |
| decision_rule_sets | 决策规则集 | AI 中枢 | 决策型智能体 |
| decision_model_registry | 决策模型注册表 | AI 中枢 | 决策型智能体 |
| execution_target_registry | 执行目标注册表 | AI 中枢 | 执行型智能体 |
| workflow_registry | workflow 调用目录 | AI 中枢 | 对话型智能体 |
| execution_runs | 流程执行实例 | AI 中枢 | |
| execution_checkpoints | 执行 checkpoint 索引 | AI 中枢 | 对接 LangGraph |
| approval_tasks | 审批运行态镜像 | AI 中枢 | 非审批主记录 |
| incidents | 监控事件聚合单 | AI 中枢 | 监控型智能体 |
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

### incidents
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | incident 主键 |
| dept_id | varchar(64) | 否 | null | index | 部门口径 |
| execution_id | uuid | 否 | null | index | 关联 execution |
| workflow_id | uuid | 否 | null | index | 关联 workflow |
| incident_type | varchar(64) | 是 |  | index | timeout/consistency/compliance/health/exception |
| severity | varchar(32) | 是 | medium | index | low/medium/high/critical |
| scope | varchar(64) | 是 | execution | index | system/workflow/execution/step |
| owner_type | varchar(32) | 否 | null |  | role/user/system |
| owner_id | varchar(64) | 否 | null | index | 责任人/角色 |
| dedup_key | varchar(255) | 是 |  | unique | 去重键 |
| status | varchar(32) | 是 | open | index | open/acknowledged/escalated/resolved/cancelled |
| summary | text | 是 |  |  | 摘要 |
| payload | jsonb | 否 | null |  | 详情 |
| escalation_at | timestamptz | 否 | null |  | 升级时间 |
| resolved_at | timestamptz | 否 | null |  | 解决时间 |
| created_at | timestamptz | 是 | now() | index | |

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

### decision_rule_sets
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 规则集主键 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| code | varchar(128) | 是 |  | unique | 规则集编码 |
| name | varchar(255) | 是 |  |  | 规则集名称 |
| status | varchar(32) | 是 | active | index | active/inactive |
| rules | jsonb | 是 |  |  | 规则内容 |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### decision_model_registry
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 模型主键 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| model_type | varchar(64) | 是 |  | index | optimization/ml/forecast |
| code | varchar(128) | 是 |  | unique | 模型编码 |
| name | varchar(255) | 是 |  |  | 模型名称 |
| config | jsonb | 是 |  |  | 模型参数与说明 |
| status | varchar(32) | 是 | active | index | active/inactive |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### execution_target_registry
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 执行目标主键 |
| dept_id | varchar(64) | 否 | null | index | 部门范围 |
| target_type | varchar(64) | 是 |  | index | go_api/feishu/email/device/file/mcp |
| code | varchar(128) | 是 |  | unique | 目标编码 |
| name | varchar(255) | 是 |  |  | 目标名称 |
| config | jsonb | 是 |  |  | 目标配置 |
| status | varchar(32) | 是 | active | index | active/inactive |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### workflow_registry
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 注册主键 |
| workflow_id | uuid | 是 |  | index | 所属 workflow |
| workflow_version | int | 是 |  | index | 发布版本 |
| dept_id | varchar(64) | 是 |  | index | 所属部门 |
| category | varchar(64) | 是 |  | index | 职能分类 |
| title | varchar(255) | 是 |  |  | 展示标题 |
| summary | text | 是 |  |  | 简介 |
| synonyms | jsonb | 否 | null |  | 同义词 |
| example_utterances | jsonb | 否 | null |  | 示例表达 |
| allowed_roles | jsonb | 否 | null |  | 允许角色 |
| required_inputs | jsonb | 否 | null |  | 必填参数 |
| input_schema | jsonb | 否 | null |  | 参数 schema |
| approval_policy | varchar(64) | 是 | risk_based |  | 审批策略 |
| risk_level | varchar(32) | 是 | medium |  | 风险等级 |
| output_contract | jsonb | 否 | null |  | 输出契约 |
| status | varchar(32) | 是 | active | index | active/inactive |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### sensor_subscriptions
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 订阅主键 |
| workflow_id | uuid | 是 |  | index | 所属 workflow |
| workflow_version | int | 是 |  | index | 所属版本 |
| node_id | varchar(128) | 是 |  | unique(workflow_id, workflow_version, node_id) | 对应感知节点 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| enabled | boolean | 是 | true | index | 是否启用 |
| source_type | varchar(32) | 是 | form_change | index | form_change/iot/third_party_notice/supply_chain_event/schedule |
| source_system | varchar(128) | 是 |  | index | 来源系统 |
| source_table | varchar(128) | 否 | null | index | 来源表 |
| source_event_key | varchar(255) | 是 |  | index | 事件源标识 |
| selected_fields | jsonb | 是 | '[]' |  | 关注字段 |
| condition_logic | varchar(16) | 是 | and |  | and/or |
| conditions | jsonb | 是 | '[]' |  | 条件数组 |
| output_event_name | varchar(255) | 是 |  |  | 输出事件名 |
| output_mapping | jsonb | 否 | null |  | 输出映射 |
| pass_raw_payload | boolean | 是 | true |  | 是否透传原始 payload |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

### sensor_event_inbox
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 事件入箱主键 |
| event_id | varchar(128) | 是 |  | unique | 上游事件 ID |
| event_type | varchar(128) | 是 |  | index | 事件类型 |
| source_system | varchar(128) | 是 |  | index | 来源系统 |
| source_table | varchar(128) | 否 | null | index | 来源表 |
| source_event_key | varchar(255) | 是 |  | index | 来源事件键 |
| dept_id | varchar(64) | 是 |  | index | 部门隔离 |
| payload | jsonb | 是 |  |  | 原始事件 payload |
| matched_subscription_ids | jsonb | 否 | null |  | 命中的订阅 |
| processing_status | varchar(32) | 是 | pending | index | pending/matched/dispatched/ignored/failed |
| error_message | text | 否 | null |  | 错误信息 |
| received_at | timestamptz | 是 | now() | index | 接收时间 |

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

约束说明：
- 同部门可有多个用户会话
- 权限相同不代表记录共享，聊天记录必须按用户隔离

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

推荐扩展字段：
- `route_type`：ask/approve/command
- `workflow_registry_match`：命中的 workflow 候选
- `message_provenance`：text/voice/pdf/image/ocr

### department_grants（建议后续补充）
| 字段 | 类型 | 必填 | 默认值 | 索引/约束 | 说明 |
|---|---|---|---|---|---|
| id | uuid | 是 |  | PK | 授权主键 |
| dept_id | varchar(64) | 是 |  | index | 部门 |
| workflow_id | uuid | 是 |  | index | workflow |
| allowed_roles | jsonb | 否 | null |  | 允许角色 |
| policy | jsonb | 否 | null |  | 附加策略 |

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
- `sensor_subscriptions` 必须绑定 `workflow_id + workflow_version + node_id`
- `sensor_event_inbox.event_id` 必须全局唯一，避免重复消费
- `workflow_registry` 只能登记已发布 workflow version
- `chat_sessions` 与 `chat_messages` 必须同时绑定 `dept_id + user_id` 语境
- 同部门用户可同权，但其消息、审批、操作记录不得混写

## 5. 隔离字段设计
- dept_id
- tenant_id（如需）

## 5.1 推荐索引
- `workflow_versions (workflow_id, version)`
- `workflow_versions (workflow_id, is_current_release)`
- `sensor_subscriptions (source_event_key, enabled)`
- `sensor_subscriptions (workflow_id, workflow_version, node_id)`
- `sensor_event_inbox (event_type, received_at)`
- `sensor_event_inbox (source_event_key, processing_status)`
- `execution_runs (workflow_id, workflow_version, status)`
- `execution_runs (dept_id, status, started_at)`
- `approval_tasks (go_approval_id)`
- `chat_messages (session_id, created_at)`
- `audit_logs (event_type, created_at)`
- `monitor_snapshots (metric_type, captured_at)`

## 6. 迁移策略
- 先建基础主表：workflows、workflow_versions、execution_runs、approval_tasks
- 第二批建支撑表：sensor_subscriptions、sensor_event_inbox、agent_memories、chat_sessions、chat_messages、tool_run_logs、audit_logs、monitor_snapshots
- 所有新增枚举值优先用 varchar + 约束控制，避免过早强绑定数据库 enum
- JSONB 字段优先用于高变结构：ui_schema、execution_dag、payload、snapshot、metadata

## 7. 待确认项
- 
