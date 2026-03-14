# 三级记忆模型设计

## 1. 总体原则
- 所有智能体共享统一记忆抽象，但不同节点按需启用
- 三级记忆为：上下文记忆、历史执行记忆、RAG 知识记忆
- 第一阶段先实现“骨架可插拔”，后续再增强召回与排序
- 任何记忆访问都必须带部门/权限上下文

## 2. 上下文记忆（Context Memory）

### 2.1 作用
- 保存当前 execution 内部的即时上下文
- 包括：用户输入、事件输入、节点输出、审批结果、临时变量

### 2.2 存储位置
- 主要在 LangGraph state 中
- 必要时落 `execution_runs.context_snapshot`

### 2.3 生命周期
- 跟随单次 execution
- execution 结束后可归档，但不作为跨流程长期知识

## 3. 历史执行记忆（Execution History Memory）

### 3.1 作用
- 保存历史决策、执行结果、异常情况、人工审批结果
- 用于同类问题参考、补偿策略、经验检索

### 3.2 推荐存储
- `agent_memories`
- `audit_logs`
- `tool_run_logs`

### 3.3 最小字段建议
| 字段 | 说明 |
|---|---|
| id | 记忆主键 |
| memory_type | execution_history |
| agent_type | 对应智能体类型 |
| dept_id | 部门隔离 |
| workflow_id | 来源工作流 |
| execution_id | 来源执行 |
| summary | 摘要 |
| payload | 结构化内容 |
| tags | 检索标签 |
| created_at | 创建时间 |

## 4. RAG 知识记忆（Knowledge Memory）

### 4.1 作用
- 保存公司 SOP、规章制度、产品说明、部门资料、FAQ、审批规则等文档知识

### 4.2 能力边界
- 支持多部门隔离
- 支持对话问答与决策引用
- 第一阶段先定义索引元数据与接口，不强制绑定具体向量库

### 4.3 推荐存储
- `rag_docs_index`：文档元数据、部门范围、状态、标签
- 向量索引：后续按选型接入

## 5. 统一访问接口建议

### 5.1 context accessor
- `get_context(key)`
- `set_context(key, value)`
- `append_context_event(event)`

### 5.2 history accessor
- `search_history(query, dept_id, agent_type)`
- `write_history(memory_record)`

### 5.3 knowledge accessor
- `search_knowledge(query, dept_id, scopes)`
- `fetch_document(doc_id)`

## 6. 各智能体的记忆使用建议

### 6.1 感知型智能体
- 必用：上下文记忆
- 可选：历史执行记忆
- 通常不直接依赖 RAG

### 6.2 决策型智能体
- 必用：上下文记忆
- 推荐：历史执行记忆
- 推荐：RAG 知识记忆

### 6.3 执行型智能体
- 必用：上下文记忆
- 推荐：历史执行记忆
- 可选：RAG（操作规范/接口说明）

### 6.4 对话型智能体
- 必用：上下文记忆
- 推荐：历史执行记忆
- 推荐：RAG 知识记忆

### 6.5 监控型智能体
- 必用：上下文记忆
- 推荐：历史执行记忆
- 可选：RAG（运维手册/异常处理手册）

## 7. 权限与隔离
- `dept_id` 必须作为所有历史记忆与知识检索的默认过滤条件
- 跨部门访问必须显式授予更高权限
- 对话型智能体调用数据库或知识库时，应优先过滤部门范围

## 8. 第一阶段实现范围
- 先实现接口层与表结构位点
- 先支持基础 summary / payload 写入
- 先支持 RAG 索引元数据，不强制完成向量召回细节
- 后续再增加重排序、引用、质量评估

## 9. 当前已落地的 runtime 级记忆实现
- `ContextMemoryAccessor` 已支持：`get_context / set_context / append_context_event`
- `HistoryMemoryAccessor` 已支持：`search_history / write_history`
- `KnowledgeMemoryAccessor` 已支持：`search_knowledge / fetch_document`
- `MemoryService.bind_runtime(state)` 已可为运行时 handler 提供统一记忆入口

当前阶段说明：
- 这些 accessor 当前以 `RuntimeState` 为底座，属于 execution 内与本地运行态级实现
- `history_memories`、`knowledge_docs` 当前先挂在 runtime state / input payload 上，目的是先把 handler 的记忆调用模式固定下来
- 后续再把历史记忆落到真实表、把知识检索接到 RAG 索引层
