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

## 2.1 按功能分类的表清单

### A. 工作流定义与发布
- `workflows`：工作流主档案
- `workflow_versions`：工作流草稿/发布版/沙盒版
- `workflow_node_configs`：节点配置拆分存储（可选）

适用场景：
- 画布搭建 workflow
- workflow 保存、编译、发布、查历史版本

### B. 运行时执行与恢复
- `execution_runs`：每次 workflow 实际执行记录
- `execution_checkpoints`：执行中断/恢复 checkpoint
- `approval_tasks`：审批运行态镜像

适用场景：
- workflow 启动
- 执行中断
- 审批恢复
- 查看执行结果

### C. 感知型智能体
- `sensor_subscriptions`：感知订阅规则
- `sensor_event_inbox`：上游事件入箱

适用场景：
- 配置数据库/事件感知节点
- 事件去重、匹配、分发

### D. 决策型智能体
- `decision_rule_sets`：规则型决策规则集
- `decision_model_registry`：模型型决策注册表

适用场景：
- 配置规则型/模型型/智能型决策
- 为 decision 节点提供可选规则和模型资源

### E. 执行型智能体
- `execution_target_registry`：执行目标目录
- `tool_run_logs`：执行工具调用轨迹

适用场景：
- 配置 Go API / department_table / 第三方执行目标
- 查看执行型节点调用过程与失败原因

### F. 对话型智能体
- `workflow_registry`：对话选流目录
- `chat_sessions`：对话会话
- `chat_messages`：对话消息与卡片
- `department_grants`（建议后续补充）：部门与 workflow 授权关系

适用场景：
- 对话型智能体从目录中选 workflow
- 记录 ask / approve / command 路由
- 保存对话上下文、审批卡片、结果回传

### G. 记忆与知识
- `agent_memories`：历史执行记忆
- `rag_docs_index`：RAG 知识索引元数据

适用场景：
- 历史执行参考
- 对话问答和决策引用知识

### H. 监控与审计
- `incidents`：监控事件聚合单
- `audit_logs`：统一审计日志
- `monitor_snapshots`：监控指标快照

适用场景：
- 监控工作台
- 审计追踪
- 异常聚合与受控干预

### I. 通用智能体配置
- `agent_configs`：五类智能体统一配置表

适用场景：
- 节点级 agent 配置存储
- 智能体配置版本化与启停控制

## 2.2 按开发步骤索引需要关注的表

### M1 基础底座
优先关注：
- `workflows`
- `workflow_versions`
- `execution_runs`
- `approval_tasks`
- `audit_logs`

用途：
- 搭 workflow 真相源
- 支撑发布状态机
- 为 execution / 审批 / 审计建立最小运行骨架

### M2 画布与工作流编排
优先关注：
- `workflows`
- `workflow_versions`
- `workflow_node_configs`（如需拆分）
- `agent_configs`
- `sensor_subscriptions`
- `sensor_event_inbox`

用途：
- 支撑画布保存、编译、发布
- 支撑感知节点配置与沙盒联调

### M3 对话视界与审批
优先关注：
- `chat_sessions`
- `chat_messages`
- `workflow_registry`
- `approval_tasks`
- `execution_runs`
- `department_grants`（若进入精细授权）

用途：
- 对话工作台
- workflow 目录检索
- ask/approve/command 路由
- 审批卡片与恢复执行

### M4 智能体能力接入
优先关注：
- `sensor_subscriptions`
- `sensor_event_inbox`
- `decision_rule_sets`
- `decision_model_registry`
- `execution_target_registry`
- `tool_run_logs`
- `agent_memories`

用途：
- 接入感知/决策/执行型智能体 handler
- 接入 Go API、department_table 和其他执行目标
- 建立历史执行参考能力

### M5 监控运维与验收
优先关注：
- `incidents`
- `audit_logs`
- `monitor_snapshots`
- `tool_run_logs`
- `execution_runs`

用途：
- 监控工作台
- 审计追踪
- 故障定位
- 发布前质量回看

> 使用规则：后续按 skill 推进开发时，先看 `implementation-plan.md` 当前处于哪一阶段，再回到这里根据阶段快速定位应重点关注的表。

## 2.3 工作流版本原则
- Python 数据库持有 workflow definitions 与 execution_dag
- `ui_schema` 与 `execution_dag` 必须分字段或分表存储
- 发布动作由 Python 完成，发布后生成不可变版本快照
- 草稿版仅用于编辑或沙盒测试，正式执行默认只读取 released 版本

## 2.4 推荐关键表

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
| target_type | varchar(64) | 是 |  | index | go_api/department_table/feishu/email/device/file/mcp |
| code | varchar(128) | 是 |  | unique | 目标编码 |
| name | varchar(255) | 是 |  |  | 目标名称 |
| config | jsonb | 是 |  |  | 目标配置 |
| status | varchar(32) | 是 | active | index | active/inactive |
| created_at | timestamptz | 是 | now() |  | |
| updated_at | timestamptz | 是 | now() |  | |

`department_table` 类型配置要求：
- `provider`：底层表格提供方，如 `bitable | spreadsheet | custom_table`
- `resource_locator`：表格资源定位信息，如应用、数据表、视图、工作簿标识
- `operation`：默认支持 `append_row`，预留 `upsert_row | update_row`
- `row_mapping`：写入字段映射规则
- `default_values`：缺省值填充
- `idempotency_key_template`：部门表格写入幂等键模板
- `writeback_policy`：写入成功后是否回填行标识或链接
- `permission_scope`：允许写入的部门、角色或 workflow 范围

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
当前实现说明：
- `sensor_subscriptions` / `sensor_event_inbox` 仍属于目标架构表设计，当前代码尚未创建这些表
- 当前临时测试链路以 `sensor_change_log` + 直接触发 execution 的方式支撑 mock records 联调
