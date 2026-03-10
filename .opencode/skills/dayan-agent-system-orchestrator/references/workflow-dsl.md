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
    "output_schema_ref": "decision.result.v1"
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

## 5. 各节点最小配置

### 5.1 sensor_agent
- `source_type`: `iot | form_change | supply_chain_event | third_party_notice | schedule`
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
    "source_system": "ERP生产库",
    "source_table": "inventory_stock",
    "source_event_key": "erp.production.db.inventory_stock",
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
- `model`：必须有 `model_type`、`model_params`、`optimization_goal`
- `llm`：必须有 `prompt_template`，推荐启用 `memory_profile` 与 `rag_refs`

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
    "recommended_quantity": 200
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
- `risk_level`：`low | medium | high`
- `recommended_actions`：推荐执行动作数组
- `explanation`：解释原因
- `citations`：仅 LLM + RAG 模式推荐返回

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
        "target_type": "go_api",
        "target_ref": "records.inventory_replenishment"
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

第一阶段最小要求：
- 可选择 `execution_target_mode`
- 可配置是否进入审批
- 审批卡片必须可投递到对话工作区
- 执行结果必须可回传到对话工作区

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
- 对每个节点补齐默认 runtime 配置
- 输出 `execution_dag` 和 `content_hash`

## 9. 执行约束
- released 模式只能执行发布版
- sandbox 模式可执行 draft，但必须显式打标，不进入正式审计统计
- 执行实例必须记录 `workflow_id + version + mode`
