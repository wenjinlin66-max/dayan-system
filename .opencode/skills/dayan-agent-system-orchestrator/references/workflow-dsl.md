# Workflow JSON DSL 设计

## 1. 设计原则
- 前端画布编辑态与执行态必须分离
- `ui_schema` 用于还原 Vue Flow 画布
- `execution_dag` 用于 Python / LangGraph 执行
- 控制节点与智能体节点统一进入一个 DSL，但类型必须显式区分
- 正式执行默认只使用 `released` 版本，草稿执行仅用于沙盒测试

## 2. 顶层结构
```json
{
  "workflow_id": "wf_purchase_approval",
  "version": 3,
  "mode": "released",
  "schema_version": "2026-03",
  "meta": {
    "name": "采购异常审批流",
    "dept_scope": ["supply_chain"],
    "tags": ["approval", "purchase"],
    "owner": "architect_user"
  },
  "ui_schema": {
    "nodes": [],
    "edges": [],
    "viewport": {}
  },
  "execution_dag": {
    "entrypoint": "sensor_1",
    "nodes": [],
    "edges": []
  }
}
```

## 3. 节点分类

### 3.1 智能体节点
- `sensor_agent`
- `decision_agent`
- `execution_agent`
- `dialog_agent`

> 说明：`monitor_agent` 不再作为普通画布节点参与 workflow 编排。监控型智能体按独立控制平面实现，在监控工作台中单独配置与运行。

### 3.2 控制节点
- `condition`
- `parallel`
- `loop`
- `subflow`
- `wait`
- `approval`
- `exception`

控制节点统一要求：
- 不直接做业务动作
- 不直接承载大模型调用
- 仅负责控制 flow 的方向、并发、等待、嵌套、审批、异常恢复

## 4. execution_dag 节点结构
```json
{
  "id": "decision_1",
  "type": "decision_agent",
  "name": "库存异常决策",
  "config": {
    "decision_mode": "llm",
    "memory_profile": {
      "context": true,
      "history": true,
      "rag": true
    },
    "prompt_template": "请根据库存异常进行处理建议",
    "rag_refs": ["kb_inventory_policy"],
    "output_template": "decision.result.v1"
  },
  "runtime": {
    "timeout_sec": 90,
    "retry_policy": {
      "max_retries": 2,
      "backoff": "exponential"
    },
    "on_error": "exception_1"
  }
}
```

### 4.1 对话触发型 workflow 的发布元数据
- 当 workflow 分类为 `dialog_trigger` 时，触发规则当前应配置在 `dialog_agent.config` 中，而不是挂在 workflow 顶层 `ui_schema.meta`
- 该配置在编辑态归属于 `dialog_agent` 节点，但发布时会被抽取并写入 `workflow_registry`，作为 chat route 的选流元数据
- 当前最小字段：`summary / synonyms / example_utterances / allowed_roles / required_inputs / input_schema`
- chat workbench 的 workflow 目录、候选检索、缺参补齐与角色过滤都应消费这组 registry 元数据，而不是临时硬编码在聊天页
- 发布新版本时，旧的 active `workflow_registry` 条目当前应先失活，再写入新版本条目；chat route / chat start 也会按 `workflow_id` 只保留最新有效条目，避免同一 dialog workflow 因多次发布在候选区重复出现

## 5. 各节点最小配置

### 5.1 sensor_agent
- `source_type`: `iot | form_change | supply_chain_event | third_party_notice | schedule | manual`
- `trigger_condition`
- `input_mapping`

推荐扩展字段：
- `source_system`
- `source_table`
- `source_event_key`
- `selected_fields`
- `condition_logic`: `and | or`
- `conditions`
- `output_event_name`
- `output_mapping`
- `pass_raw_payload`

数据库实时感知第一阶段推荐示例：
```json
{
  "id": "sensor_db_inventory",
  "type": "sensor_agent",
  "name": "库存变更感知",
  "config": {
    "source_type": "form_change",
    "source_system": "erp_prod",
    "source_table": "inventory_stock",
    "source_event_key": "record.updated",
    "selected_fields": ["item_id", "stock_count", "safety_limit", "warehouse_id"],
    "condition_logic": "and",
    "conditions": [
      {
        "field": "stock_count",
        "operator": "<",
        "value_from_field": "safety_limit"
      }
    ],
    "output_event_name": "inventory.low_stock.detected",
    "output_mapping": {
      "item_id": "payload.item_id",
      "stock_count": "payload.stock_count",
      "safety_limit": "payload.safety_limit",
      "warehouse_id": "payload.warehouse_id"
    },
    "pass_raw_payload": true
  }
}
```

当前阶段补充口径：
- `source_system / source_table / source_event_key / selected_fields / conditions` 在前端应优先通过后端 `sensor-metadata` 目录接口下拉选择，而不是依赖自由输入
- `payload.*` 输出映射默认面向数据库变更事件的 `after` 快照；若要读取原始事件信封，则使用 `event.*`

### 5.2 decision_agent
- `decision_mode`: `rule | model | llm`
- `prompt_template`
- `memory_profile`
- `rag_refs`

推荐扩展字段：
- `rule_set_ref`
- `rule_config`
- `model_type`
- `model_ref`
- `model_params`
- `optimization_goal`
- `constraints`
- `output_template`
- `include_explanation`
- `include_citations`

决策型节点推荐示例：
```json
{
  "id": "decision_inventory_policy",
  "type": "decision_agent",
  "name": "库存补货决策",
  "config": {
    "decision_mode": "rule",
    "rule_set_ref": "inventory_replenishment_rules",
    "rule_config": {
      "severity_levels": ["low", "medium", "high"]
    },
    "output_template": "decision.result.v1",
    "include_explanation": true,
    "include_citations": false
  },
  "runtime": {
    "timeout_sec": 30,
    "retry_policy": {
      "max_retries": 1,
      "backoff": "fixed"
    },
    "on_error": "exception_1"
  }
}
```

三种模式最小要求：
- `rule`：必须有 `rule_set_ref` 或 `rule_config`
- `model`：必须有 `model_type`、`optimization_goal`；`model_params` 当前为推荐项，未配置时使用默认权重/容量边界
- `llm`：必须有 `prompt_template`，推荐启用 `memory_profile` 与 `rag_refs`

当前实现补充口径：
- `rule_config` 当前已开始承担规则型详细设计：至少可承载 `severity_thresholds / severity_field / target_item_field / quantity_field / action_type`
- `model_params` 当前已开始承载模型型详细设计：至少可承载 `objective_weights / capacity_limits / candidate_actions`
- `output_template / include_explanation / include_citations` 当前已进入前端配置与 LLM 模式运行提示，用于约束智能型输出格式与解释强度
- 编译阶段当前已开始校验 `decision_agent`：`decision_mode` 合法性、三模式必填字段、`constraints / rag_refs` 数组类型，以及 `include_explanation / include_citations` 的布尔值约束

## 5.2.1 决策型统一输出结构
推荐所有决策型节点统一输出：

```json
{
  "decision_mode": "rule",
  "decision_summary": "库存低于安全阈值，建议发起补货审批",
  "decision_payload": {
    "severity": "high",
    "target_item_id": "A-1001",
    "target_warehouse_id": "W-01",
    "target_dept_id": "production",
    "recommended_quantity": 200,
    "chat_report": {
      "title": "库存风险预警",
      "content": "A-1001 库存低于安全库存，建议立即补货并通知生产部门关注。",
      "audience": "production"
    },
    "table_write": {
      "item_id": "A-1001",
      "warehouse_id": "W-01",
      "current_stock": 16,
      "safety_limit": 20,
      "recommended_quantity": 200,
      "status": "待处理"
    }
  },
  "risk_level": "medium",
  "recommended_actions": [
    {
      "action_type": "create_replenishment_request",
      "params": {
        "item_id": "A-1001",
        "quantity": 200
      }
    }
  ],
  "explanation": "当前库存低于 safety_limit，满足规则触发条件。",
  "citations": []
}
```

字段要求：
- `decision_mode`：`rule | model | llm`
- `decision_summary`：给人读的简要结论
- `decision_payload`：结构化业务结果
- `decision_payload.chat_report`：供 `department_chat` 执行节点直接消费的风险报告块
- `decision_payload.table_write`：供 `department_table` 执行节点直接消费的结构化写表块
- `risk_level`：`low | medium | high`
- `recommended_actions`：推荐执行动作数组
- `explanation`：解释原因
- `citations`：仅 LLM + RAG 模式推荐返回
- 决策型只输出 **一份统一结构化结果**；后续 `parallel` 后的多个执行型节点共享消费这同一份结果，而不是由决策型分别给每个执行型单独发不同内容

### 5.3 execution_agent
- `tool_mode`: `manual | auto`
- `tool_refs`
- `approval_required`
- `result_delivery`: `chat | event | monitor`

推荐扩展字段：
- `execution_target_mode`: `manual | ai_select`
- `execution_targets`
- `approval_mode`: `always | risk_based | never`
- `approval_required`
- `approval_card_template`
- `chat_delivery`
- `result_template`
- `failure_delivery`

`execution_targets` 中推荐支持的 `target_type`：
- `go_api`
- `department_chat`
- `department_table`
- `feishu`
- `email`
- `device`
- `file`
- `mcp`

当前执行型节点新口径：
- 一个 `execution_agent` 默认表达 **一个执行目标语义**，例如“发送部门对话框风险报告”或“写入部门业务表”
- 若业务上既要“发送风险报告到对话框”又要“修改业务表格/调用第三方”，应在 `decision_agent` 后通过 `parallel` 节点并列挂多个 `execution_agent`
- `execution_target_mode=ai_select` 的含义是：在当前 execution 节点的候选目标集合中，由 AI 选择一个最合适的目标执行；它不替代多节点并列执行
- `approval_required / approval_mode` 属于 execution 节点自身能力：命中审批后在当前 execution 节点挂起，审批通过后继续执行该 execution 节点，而不是必须额外插一个 approval 节点

执行型节点推荐示例：
```json
{
  "id": "execution_replenishment",
  "type": "execution_agent",
  "name": "补货执行",
  "config": {
    "execution_target_mode": "manual",
    "execution_targets": [
      {
        "target_type": "department_table",
        "target_ref": "dept_table.production.replenishment_register",
        "operation": "append_row"
      }
    ],
    "approval_mode": "risk_based",
    "approval_required": true,
    "approval_card_template": "approval.replenishment.v1",
    "result_delivery": "chat",
    "chat_delivery": {
      "send_summary": true,
      "send_failure_reason": true
    }
  }
}
```

`department_table` 目标推荐配置字段：
- `target_ref`：执行目标注册表中的目标编码
- `provider`：底层表格提供方，如 `bitable | spreadsheet | custom_table`
- `operation`：`append_row | upsert_row | update_row | append_rows | upsert_rows | replace_rows`
- `sheet_locator`：表格/数据表定位信息
- `dept_route_mode`：`current_dept | fixed_dept | derived`
- `row_mapping`：字段映射规则
- `default_values`：缺省值注入
- `idempotency_key_template`：防重复写入模板
- `write_result_contract`：写入后回传结构
- `row_mapping` 当前除 `decision_payload.* / dept_id / risk_level` 外，还可直接使用 `sensor_payload.*` 与 `event.*`；因此 `sensor_agent -> execution_agent` 型事件流程已经可以直接把感知结果写入下游表
- 批量写表时，`execution_agent` 当前还支持：
  - `rows_payload`：多行结构化记录数组
  - `replace_by_field` / `replace_by_value`：用于 `replace_rows` 先删旧再重建

执行型节点当前补充口径：
- `target_type=department_chat` 表示该 execution 节点的主目标就是“把决策结果发送到目标部门对话框”，不是结果回传的副作用
- `target_type=department_table` 表示该 execution 节点的主目标是写表；如仍需要把执行结果摘要通知到对话区，可继续使用 `result_delivery`
- `result_target_dept_id` 用于显式指定 chat 报告或结果摘要的目标部门；未配置时优先从 `decision_payload.target_dept_id / decision_payload.dept_id` 推导，否则回退当前执行部门
- `result_template` 用于自定义 `department_chat` 目标的报告正文，支持 `{{decision_summary}} / {{risk_level}} / {{decision_explanation}} / {{recommended_actions}} / {{target_item_id}} / {{recommended_quantity}} / {{result_summary}}` 等变量
- `chat_delivery.send_summary` 控制默认报告首段是否包含风险摘要；`chat_delivery.send_failure_reason` 为失败态报告预留配置位
- 当前运行时已开始支持 `parallel` 节点的最小分支调度，用于在 `decision -> parallel -> 多 execution_agent` 口径下顺序执行并列分支；后续再继续增强为更完整的 fork/join 语义

`department_table` 推荐示例：
```json
{
  "id": "execution_dept_register",
  "type": "execution_agent",
  "name": "部门台账登记",
  "config": {
    "execution_target_mode": "manual",
    "execution_targets": [
      {
        "target_type": "department_table",
        "target_ref": "dept_table.production.replenishment_register",
        "provider": "bitable",
        "operation": "append_row",
        "dept_route_mode": "current_dept",
        "sheet_locator": {
          "app_token": "dept_app_placeholder",
          "table_id": "tbl_replenishment"
        },
        "row_mapping": {
          "物料编码": "decision_payload.target_item_id",
          "仓库": "decision_payload.target_warehouse_id",
          "建议补货量": "decision_payload.recommended_quantity",
          "风险等级": "risk_level"
        },
        "default_values": {
          "状态": "待处理"
        },
        "idempotency_key_template": "{{dept_id}}:{{execution_id}}:{{node_id}}",
        "write_result_contract": {
          "return_row_id": true,
          "return_sheet_name": true
        }
      }
    ],
    "approval_mode": "risk_based",
    "approval_required": true,
    "result_delivery": "chat"
  }
}
```

`parts_demand` 下发表单当前最小示例：
```json
{
  "id": "execution_purchase_request",
  "type": "execution_agent",
  "name": "采购表单下发",
  "config": {
    "approval_required": false,
    "approval_mode": "never",
    "execution_target_mode": "manual",
    "execution_targets": [
      {
        "target_type": "department_table",
        "target_ref": "purchase_request",
        "provider": "custom_table",
        "operation": "append_row",
        "row_mapping": {
          "order_no": "sensor_payload.order_no",
          "product_code": "sensor_payload.product_code",
          "part_code": "sensor_payload.part_code",
          "part_name": "sensor_payload.part_name",
          "request_qty": "sensor_payload.purchase_qty",
          "estimated_cost": "sensor_payload.total_cost"
        },
        "default_values": {
          "supplier_hint": "待采购/销售确认供应来源",
          "request_status": "pending"
        }
      }
    ]
  }
}
```

链路二 projection workflow 当前最小示例：
```json
{
  "id": "execution_parts_demand",
  "type": "execution_agent",
  "name": "重建零件需求表",
  "config": {
    "execution_target_mode": "manual",
    "execution_targets": [
      {
        "target_type": "department_table",
        "target_ref": "parts_demand",
        "provider": "custom_table",
        "operation": "replace_rows",
        "replace_by_field": "order_no",
        "replace_by_value": "decision_payload.replace_by.value",
        "record_key_template": "{{payload.order_no}}:{{payload.part_code}}:{{payload.source_type}}"
      }
    ]
  }
}
```

第一阶段最小要求：
- 可选择 `execution_target_mode`
- 可配置并使用 `department_table` 执行目标
- 可配置是否进入审批
- 审批卡片必须可投递到对话工作区
- 执行结果必须可回传到对话工作区
- 执行型节点应支持“只发部门对话框报告、不做数据库写入”的 chat-only 路径，用于风险提示、告警播报、第三方消息转述等轻执行场景

### 5.4 dialog_agent
- `entry_mode`: `ask | approve | command`
- `allowed_data_scopes`
- `rag_refs`
- `supports`: `text | voice | pdf`

推荐扩展字段：
- `dept_scope`
- `allowed_workflow_categories`
- `workflow_registry_scope`
- `routing_policy`
- `disambiguation_policy`
- `approval_workspace_enabled`
- `multimodal_enabled`
- `attachment_types`

对话型节点推荐示例：
```json
{
  "id": "dialog_department_router",
  "type": "dialog_agent",
  "name": "生产部对话路由器",
  "config": {
    "entry_mode": "command",
    "dept_scope": ["production"],
    "allowed_data_scopes": ["production", "inventory"],
    "workflow_registry_scope": ["production"],
    "allowed_workflow_categories": ["inventory", "approval", "device"],
    "routing_policy": "registry_first",
    "disambiguation_policy": "ask_user_when_ambiguous",
    "approval_workspace_enabled": true,
    "multimodal_enabled": true,
    "attachment_types": ["text", "voice", "pdf", "image"],
    "rag_refs": ["kb_production_rules"]
  }
}
```

对话型节点主逻辑要求：
- 必须先判断输入属于 `ask / approve / command`
- `command` 路径必须先查 workflow 注册目录，再做权限和参数校验
- 候选 workflow 多于一个且无明显优先项时，必须进入澄清/确认步骤

### 5.5 monitor_agent
监控型智能体不作为普通 execution_dag 节点使用。

如果未来确有业务需要在某条 workflow 中显式发出监控提示，建议后续增加轻量辅助节点（如 `emit-monitor-signal`），而不是把监控型智能体本体做成 workflow 节点。

### 5.6 approval
- `approval_type`
- `approver_scope`
- `card_template`
- `resume_mapping`

## 6. 边结构
```json
{
  "id": "edge_1",
  "source": "sensor_1",
  "target": "decision_1",
  "condition": null,
  "label": "库存异常进入决策"
}
```

## 7. 条件与并行规则
- `condition` 节点只负责分流，不直接做业务动作
- `parallel` 节点必须定义 fork 与 join 规则
- `loop` 节点必须显式给出退出条件或最大次数
- `subflow` 节点必须引用已发布的子流程版本

### 7.1 各控制节点最小配置

#### `condition`
- `expression`
- `branches`
- `default_branch`

#### `parallel`
- `branches`
- `join_mode`
- `join_timeout_sec`

#### `loop`
- `loop_mode`: `count | until`
- `max_iterations`
- `until_expression`

#### `subflow`
- `subflow_workflow_id`
- `subflow_version`
- `input_mapping`

#### `wait`
- `wait_type`: `duration | event`
- `duration_sec`
- `resume_event_key`

#### `approval`
- `approval_type`
- `approver_scope`
- `card_template`
- `resume_mapping`

#### `exception`
- `handle_mode`
- `fallback_action`
- `notify_targets`

## 8. 编译规则
- 去除画布坐标、颜色、缩放等纯 UI 字段
- 校验节点连通性、entrypoint 唯一性、环路合法性
- `sensor_agent`、`decision_agent` 当前必须至少连接一个下游节点；若无 outgoing edge，则编译失败，避免发布出“只有感知/决策输出但无后继链路”的假闭环 workflow
- 对每个节点补齐默认 runtime 配置
- 输出 `execution_dag` 和 `content_hash`

## 9. 执行约束
- released 模式只能执行发布版
- sandbox 模式可执行 draft，但必须显式打标，不进入正式审计统计
- 执行实例必须记录 `workflow_id + version + mode`
