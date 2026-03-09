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
- `monitor_agent`

### 3.2 控制节点
- `condition`
- `parallel`
- `loop`
- `subflow`
- `wait`
- `approval`
- `exception`

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

### 5.2 decision_agent
- `decision_mode`: `rule | model | llm`
- `prompt_template`
- `memory_profile`
- `rag_refs`

### 5.3 execution_agent
- `tool_mode`: `manual | auto`
- `tool_refs`
- `approval_required`
- `result_delivery`: `chat | event | monitor`

### 5.4 dialog_agent
- `entry_mode`: `ask | approve | command`
- `allowed_data_scopes`
- `rag_refs`
- `supports`: `text | voice | pdf`

### 5.5 monitor_agent
- `watch_targets`
- `thresholds`
- `report_channel`

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

## 8. 编译规则
- 去除画布坐标、颜色、缩放等纯 UI 字段
- 校验节点连通性、entrypoint 唯一性、环路合法性
- 对每个节点补齐默认 runtime 配置
- 输出 `execution_dag` 和 `content_hash`

## 9. 执行约束
- released 模式只能执行发布版
- sandbox 模式可执行 draft，但必须显式打标，不进入正式审计统计
- 执行实例必须记录 `workflow_id + version + mode`
