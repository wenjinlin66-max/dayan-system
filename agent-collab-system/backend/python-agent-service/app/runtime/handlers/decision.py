from __future__ import annotations

import httpx
from math import ceil

from typing import cast
from sqlalchemy import select

from app.domain.memory.service import MemoryService, RuntimeMemoryBundle
from app.db.session import get_mock_session_factory
from app.integrations.llm.client import LLMClient
from app.mock_records.db.models import ProductBomRecord
from app.runtime.models import JsonValue, NodeExecutionResult, RuntimeNode, RuntimeState


class DecisionNodeHandler:
    llm_client: LLMClient

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient.from_settings()

    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        memory = MemoryService.bind_runtime(state)
        input_values = state.input_payload.get("input_values")
        payload = self._resolve_decision_payload(
            cast(dict[str, JsonValue], input_values) if isinstance(input_values, dict) else state.input_payload,
            state=state,
        )
        decision_mode = str(node.config.get("decision_mode") or "rule")
        decision_output = await self._build_decision_output(node, payload, state, decision_mode, memory)
        state.decision_outputs[node.id] = cast(dict[str, object], decision_output)
        memory.context.set_context("latest_decision_node", node.id)
        history_record: dict[str, JsonValue] = {
            "memory_type": "execution_history",
            "agent_type": "decision_agent",
            "workflow_id": state.workflow_id,
            "execution_id": state.execution_id,
            "summary": str(decision_output.get("decision_summary") or f"{node.name} 完成决策"),
            "payload": decision_output,
            "mode": decision_mode,
        }
        memory.history.write_history(history_record)
        return NodeExecutionResult(next_node_id=next_nodes[0] if next_nodes else None)

    async def _build_decision_output(
        self,
        node: RuntimeNode,
        payload: dict[str, JsonValue],
        state: RuntimeState,
        decision_mode: str,
        memory: RuntimeMemoryBundle,
    ) -> dict[str, JsonValue]:
        if decision_mode == "model":
            return self._build_model_output(node, payload, state)
        if decision_mode == "llm":
            return await self._build_llm_output(node, payload, state, memory)
        return await self._build_rule_output(node, payload, state)

    @staticmethod
    def _resolve_decision_payload(payload: dict[str, JsonValue], *, state: RuntimeState) -> dict[str, JsonValue]:
        latest_sensor = next(reversed(state.sensor_outputs.values()), None)
        if isinstance(latest_sensor, dict):
            raw_sensor_payload = latest_sensor.get("payload")
            if isinstance(raw_sensor_payload, dict):
                merged: dict[str, JsonValue] = dict(cast(dict[str, JsonValue], raw_sensor_payload))
                merged.update(payload)
                return merged
        return payload

    async def _build_rule_output(self, node: RuntimeNode, payload: dict[str, JsonValue], state: RuntimeState) -> dict[str, JsonValue]:
        _ = state
        base_payload = payload
        rule_config = DecisionNodeHandler._object_dict(node.config.get("rule_config"))
        rule_set_ref = DecisionNodeHandler._string_value(node.config.get("rule_set_ref"), default="default_rule_set")
        if rule_set_ref == "parts_demand_projection":
            return await self._build_parts_demand_projection_output(node, payload, state)
        severity_thresholds = DecisionNodeHandler._float_dict(rule_config.get("severity_thresholds"), {"high": 0.3, "medium": 0.8, "low": 1.0})
        target_item_field = DecisionNodeHandler._string_value(rule_config.get("target_item_field"), default="item_id")
        quantity_field = DecisionNodeHandler._string_value(rule_config.get("quantity_field"), default="recommended_quantity")
        severity_field = DecisionNodeHandler._string_value(rule_config.get("severity_field"), default="severity")
        action_type = DecisionNodeHandler._string_value(rule_config.get("action_type"), default="create_department_table_record")

        current_stock = DecisionNodeHandler._number_value(base_payload.get("stock_count") or base_payload.get("current_stock"))
        safety_limit = DecisionNodeHandler._number_value(base_payload.get("safety_limit") or base_payload.get("target_stock"))
        explicit_quantity = DecisionNodeHandler._number_value(base_payload.get(quantity_field) or payload.get(quantity_field))
        gap = max((safety_limit or 0) - (current_stock or 0), 0)
        recommended_quantity = int(explicit_quantity or max(ceil(gap * 1.5), 100))
        ratio = ((current_stock or 0) / safety_limit) if current_stock is not None and safety_limit not in (None, 0) else None
        severity = DecisionNodeHandler._resolve_severity(ratio, severity_thresholds)
        target_item = base_payload.get(target_item_field) or base_payload.get("target_item_id") or "unknown-item"

        return {
            "decision_mode": "rule",
            "decision_summary": f"{node.name} 根据规则集 {str(node.config.get('rule_set_ref') or 'default_rule_set')} 生成执行建议",
            "decision_payload": DecisionNodeHandler._build_standard_decision_payload(
                {
                    severity_field: severity,
                    "target_item_id": target_item,
                    "current_stock": current_stock,
                    "safety_limit": safety_limit,
                    "gap": gap,
                    "recommended_quantity": recommended_quantity,
                    "rule_set_ref": rule_set_ref,
                }
            ),
            "risk_level": severity if severity in {"low", "medium"} else "high",
            "recommended_actions": [
                {
                    "action_type": action_type,
                    "params": {
                        "item_id": target_item,
                        "quantity": recommended_quantity,
                        severity_field: severity,
                    },
                }
            ],
            "explanation": f"根据库存/阈值规则判断当前缺口为 {gap}，库存比例为 {ratio if ratio is not None else 'unknown'}，因此输出 {severity} 级决策。",
            "citations": [],
        }

    async def _build_parts_demand_projection_output(
        self,
        node: RuntimeNode,
        payload: dict[str, JsonValue],
        state: RuntimeState,
    ) -> dict[str, JsonValue]:
        order_no = self._string_value(payload.get("order_no"), default="")
        customer_name = self._string_value(payload.get("customer_name"), default="")
        product_code = self._string_value(payload.get("product_code"), default="")
        product_name = self._string_value(payload.get("product_name"), default="")
        ordered_qty = self._coerce_int(payload.get("ordered_qty"))
        raw_event = state.input_payload.get("event")
        event_envelope = cast(dict[str, JsonValue], raw_event) if isinstance(raw_event, dict) else {}
        raw_event_payload = event_envelope.get("payload")
        event_payload = cast(dict[str, JsonValue], raw_event_payload) if isinstance(raw_event_payload, dict) else {}
        operation = str(event_payload.get("operation") or "")

        if operation == "deleted":
            return {
                "decision_mode": "rule",
                "decision_summary": f"{node.name} 已清理被删除订单对应的零件需求投影",
                "decision_payload": {
                    "projection_type": "parts_demand_projection",
                    "source_table": "customer_order",
                    "target_table": "parts_demand",
                    "order_no": order_no,
                    "replace_by": {
                        "field": "order_no",
                        "value": order_no,
                    },
                    "table_write": {},
                    "table_writes": [],
                    "chat_report": {
                        "title": "订单删除已同步需求清理",
                        "content": f"订单 {order_no or '未命名订单'} 的零件需求及下游分发表已清理。",
                        "audience": "supply_chain",
                    },
                },
                "risk_level": "low",
                "recommended_actions": [
                    {
                        "action_type": "replace_department_table_rows",
                        "params": {
                            "target_ref": "parts_demand",
                            "replace_by_field": "order_no",
                            "replace_by_value": order_no,
                            "row_count": 0,
                        },
                    }
                ],
                "explanation": f"订单 {order_no or '未命名订单'} 已删除，因此需要清理对应的 parts_demand 与下游分发表。",
                "citations": [],
            }

        bom_rows = await self._load_bom_rows(product_code)
        table_writes: list[dict[str, JsonValue]] = []
        aggregated: dict[tuple[str, str], dict[str, JsonValue]] = {}
        for bom in bom_rows:
            required_qty = max(0, ordered_qty * self._coerce_int(bom.qty_per_unit))
            source_type = self._normalize_source_type(bom.source_type)
            key = (str(bom.part_code), source_type)
            purchase_qty = required_qty if source_type == "purchase" else 0
            manufacture_qty = required_qty if source_type == "manufacture" else 0
            customer_qty = required_qty if source_type == "customer" else 0
            existing = aggregated.get(key)
            if existing is None:
                aggregated[key] = {
                    "id": f"dem_{order_no}_{bom.part_code}_{source_type}",
                    "order_no": order_no,
                    "customer_name": customer_name,
                    "product_code": product_code,
                    "product_name": product_name,
                    "part_code": str(bom.part_code),
                    "part_name": str(bom.part_name),
                    "source_type": source_type,
                    "required_qty": required_qty,
                    "purchase_qty": purchase_qty,
                    "manufacture_qty": manufacture_qty,
                    "customer_qty": customer_qty,
                    "unit_cost": float(bom.unit_cost or 0),
                    "total_cost": round(required_qty * float(bom.unit_cost or 0), 2),
                }
                continue
            existing["required_qty"] = self._coerce_int(cast(object | None, existing.get("required_qty"))) + required_qty
            existing["purchase_qty"] = self._coerce_int(cast(object | None, existing.get("purchase_qty"))) + purchase_qty
            existing["manufacture_qty"] = self._coerce_int(cast(object | None, existing.get("manufacture_qty"))) + manufacture_qty
            existing["customer_qty"] = self._coerce_int(cast(object | None, existing.get("customer_qty"))) + customer_qty
            existing["total_cost"] = round(self._coerce_float(cast(object | None, existing.get("total_cost"))) + required_qty * float(bom.unit_cost or 0), 2)

        table_writes = list(aggregated.values())
        decision_payload: dict[str, JsonValue] = {
            "projection_type": "parts_demand_projection",
            "source_table": "customer_order",
            "target_table": "parts_demand",
            "order_no": order_no,
            "product_code": product_code,
            "product_name": product_name,
            "customer_name": customer_name,
            "ordered_qty": ordered_qty,
            "replace_by": {
                "field": "order_no",
                "value": order_no,
            },
            "table_write": table_writes[0] if table_writes else {},
            "table_writes": cast(JsonValue, table_writes),
            "chat_report": {
                "title": "订单已完成零件需求拆解",
                "content": f"订单 {order_no or '未命名订单'} 已按产品 BOM 生成 {len(table_writes)} 条零件需求。",
                "audience": "supply_chain",
            },
        }
        return {
            "decision_mode": "rule",
            "decision_summary": f"{node.name} 已根据产品 BOM 生成零件需求投影",
            "decision_payload": decision_payload,
            "risk_level": "low",
            "recommended_actions": [
                {
                    "action_type": "replace_department_table_rows",
                    "params": {
                        "target_ref": "parts_demand",
                        "replace_by_field": "order_no",
                        "replace_by_value": order_no,
                        "row_count": len(table_writes),
                    },
                }
            ],
            "explanation": f"基于 {product_code or 'unknown-product'} 的 BOM 展开订单数量 {ordered_qty}，重建对应 parts_demand。",
            "citations": [],
        }

    @staticmethod
    async def _load_bom_rows(product_code: str) -> list[ProductBomRecord]:
        if not product_code:
            return []
        async with get_mock_session_factory()() as session:
            result = await session.execute(
                select(ProductBomRecord).where(ProductBomRecord.product_code == product_code).order_by(ProductBomRecord.updated_at.desc())
            )
            return list(result.scalars().all())

    @staticmethod
    def _coerce_int(value: object | None) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value.strip() or "0"))
            except ValueError:
                return 0
        return 0

    @staticmethod
    def _coerce_float(value: object | None) -> float:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip() or "0")
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def _normalize_source_type(value: object | None) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"purchase", "采购", "buy", "purchasing", "采购件"}:
            return "purchase"
        if normalized in {"manufacture", "生产", "制造", "自制", "manufacturing"}:
            return "manufacture"
        if normalized in {"customer", "客户提供", "客户供料", "客供", "客户", "customer_supply"}:
            return "customer"
        return "purchase"

    @staticmethod
    def _build_model_output(node: RuntimeNode, payload: dict[str, JsonValue], state: RuntimeState) -> dict[str, JsonValue]:
        optimization_goal = str(node.config.get("optimization_goal") or "balance_cost_and_efficiency")
        raw_constraints = node.config.get("constraints")
        constraints = [item for item in cast(list[object], raw_constraints)] if isinstance(raw_constraints, list) else []
        model_type = str(node.config.get("model_type") or "scorecard")
        model_ref = str(node.config.get("model_ref") or f"{model_type}.default")
        model_params = DecisionNodeHandler._object_dict(node.config.get("model_params"))
        objective_weights = DecisionNodeHandler._float_dict(model_params.get("objective_weights"), {
            "cost": 0.35,
            "timeliness": 0.4,
            "stability": 0.25,
        })
        capacity_limits = DecisionNodeHandler._float_dict(model_params.get("capacity_limits"), {
            "max_quantity": 500,
            "min_quantity": 20,
        })
        candidate_actions = DecisionNodeHandler._string_list(model_params.get("candidate_actions"), [
            "append_row",
            "request_approval",
            "notify_manager",
        ])
        target_item = payload.get("item_id") or payload.get("target_item_id") or state.context.get("target_item_id") or "unknown-item"
        current_stock = DecisionNodeHandler._number_value(payload.get("stock_count") or state.context.get("stock_count"))
        safety_limit = DecisionNodeHandler._number_value(payload.get("safety_limit") or state.context.get("safety_limit"))
        demand_gap = max((safety_limit or 0) - (current_stock or 0), 0)
        demand_pressure = min(demand_gap / max(safety_limit or 1, 1), 2.0)
        recommended_quantity = DecisionNodeHandler._clamp_quantity(
            int(ceil(max(demand_gap, 20) * DecisionNodeHandler._model_factor(model_type, optimization_goal))),
            minimum=int(capacity_limits.get("min_quantity", 20)),
            maximum=int(capacity_limits.get("max_quantity", 500)),
        )
        best_action, action_scores = DecisionNodeHandler._score_candidate_actions(
            candidate_actions=candidate_actions,
            objective_weights=objective_weights,
            optimization_goal=optimization_goal,
            demand_pressure=demand_pressure,
        )
        risk_level = "high" if demand_pressure >= 1 else "medium" if demand_pressure >= 0.45 else "low"
        return {
            "decision_mode": "model",
            "decision_summary": f"{node.name} 基于 {model_ref} 完成 {optimization_goal} 优化决策",
            "decision_payload": DecisionNodeHandler._build_standard_decision_payload(
                {
                    "target_item_id": target_item,
                    "model_type": model_type,
                    "model_ref": model_ref,
                    "optimization_goal": optimization_goal,
                    "constraint_count": len(constraints),
                    "current_stock": current_stock,
                    "safety_limit": safety_limit,
                    "demand_pressure": round(demand_pressure, 3),
                    "recommended_quantity": recommended_quantity,
                    "best_action": best_action,
                    "action_scores": action_scores,
                }
            ),
            "risk_level": risk_level,
            "recommended_actions": [
                {
                    "action_type": best_action,
                    "params": {
                        "item_id": target_item,
                        "optimization_goal": optimization_goal,
                        "recommended_quantity": recommended_quantity,
                        "model_ref": model_ref,
                    },
                }
            ],
            "explanation": f"基于目标权重 {objective_weights}、候选动作 {candidate_actions} 与需求压力 {round(demand_pressure, 3)} 计算优先级，选择 {best_action}。",
            "citations": [],
        }

    async def _build_llm_output(
        self,
        node: RuntimeNode,
        payload: dict[str, JsonValue],
        state: RuntimeState,
        memory: RuntimeMemoryBundle,
    ) -> dict[str, JsonValue]:
        _ = state
        prompt_template = str(node.config.get("prompt_template") or "")
        optimization_goal = str(node.config.get("optimization_goal") or "balance_cost_and_explainability")
        constraints = DecisionNodeHandler._string_list(node.config.get("constraints"), [])
        output_template = str(node.config.get("output_template") or "decision.result.v1")
        include_explanation = bool(node.config.get("include_explanation", True))
        include_citations = bool(node.config.get("include_citations", True))
        query = str(payload.get("message") or payload.get("query") or node.name)
        target_item_id = payload.get("item_id") or payload.get("target_item_id") or state.context.get("target_item_id") or "unknown-item"
        current_stock = DecisionNodeHandler._number_value(payload.get("stock_count") or state.context.get("stock_count"))
        safety_limit = DecisionNodeHandler._number_value(payload.get("safety_limit") or state.context.get("safety_limit"))
        recommended_quantity = int(max(ceil(max((safety_limit or 0) - (current_stock or 0), 0) * 1.2), 20))
        rag_refs_raw = node.config.get("rag_refs")
        rag_refs = [item for item in cast(list[object], rag_refs_raw)] if isinstance(rag_refs_raw, list) else []
        rag_scopes = [item for item in rag_refs if isinstance(item, str)]
        knowledge_hits = memory.knowledge.search_knowledge(query, scopes=rag_scopes)
        history_hits = memory.history.search_history(query, agent_type="decision_agent")
        fallback = cast(
            dict[str, JsonValue],
            {
                "decision_mode": "llm",
                "decision_summary": f"{node.name} 结合知识记忆生成一次智能决策建议",
                "decision_payload": {
                    "query": query,
                    "target_item_id": target_item_id,
                    "current_stock": current_stock,
                    "safety_limit": safety_limit,
                    "prompt_template": prompt_template,
                    "optimization_goal": optimization_goal,
                    "output_template": output_template,
                    "knowledge_hit_count": len(knowledge_hits),
                    "history_hit_count": len(history_hits),
                    "recommended_quantity": recommended_quantity,
                    "decision_basis": "fallback_from_runtime_context",
                    "next_step": "review_and_execute",
                },
                "risk_level": "medium",
                "recommended_actions": [
                    {
                        "action_type": "llm_generated_recommendation",
                        "params": {
                            "query": query,
                            "item_id": target_item_id,
                            "quantity": recommended_quantity,
                            "output_template": output_template,
                        },
                    }
                ],
                "explanation": "已接入智能型决策链路，但当前使用 fallback 结构返回，建议检查网关或提示模板。" if include_explanation else "",
                "citations": [
                    {
                        "doc_id": str(item.get("doc_id") or ""),
                        "title": str(item.get("title") or ""),
                    }
                    for item in knowledge_hits[:3]
                ] if include_citations else [],
            },
        )
        if not self.llm_client.enabled:
            return fallback

        messages = self._build_llm_messages(
            node_name=node.name,
            query=query,
            prompt_template=prompt_template,
            optimization_goal=optimization_goal,
            constraints=constraints,
            output_template=output_template,
            include_explanation=include_explanation,
            include_citations=include_citations,
            payload=payload,
            knowledge_hits=knowledge_hits,
            history_hits=history_hits,
        )
        try:
            llm_payload = await self.llm_client.chat_json(messages=messages)
        except (httpx.HTTPError, RuntimeError):
            return fallback

        return self._normalize_llm_output(node_name=node.name, raw=llm_payload, fallback=fallback, input_payload=payload)

    @staticmethod
    def _build_llm_messages(
        *,
        node_name: str,
        query: str,
        prompt_template: str,
        optimization_goal: str,
        constraints: list[str],
        output_template: str,
        include_explanation: bool,
        include_citations: bool,
        payload: dict[str, JsonValue],
        knowledge_hits: list[dict[str, JsonValue]],
        history_hits: list[dict[str, JsonValue]],
    ) -> list[dict[str, str]]:
        knowledge_text = "\n".join(
            f"- {item.get('title') or item.get('doc_id')}: {item.get('content') or ''}"
            for item in knowledge_hits[:5]
        ) or "无"
        history_text = "\n".join(
            f"- {item.get('summary') or ''}"
            for item in history_hits[-5:]
        ) or "无"
        return [
            {
                "role": "system",
                "content": (
                    "你是大衍系统中的决策型智能体。"
                    "请基于输入、知识摘要和历史摘要输出严格 JSON 对象，不要输出 Markdown。"
                    "JSON 必须包含 decision_summary、decision_payload、risk_level、recommended_actions、explanation、citations。"
                    "decision_payload 必须稳定包含 chat_report 与 table_write 两个子对象，供不同执行型节点消费。"
                    "risk_level 只能是 low、medium、high。"
                ),
            },
            {
                "role": "system",
                "content": (
                    f"节点名称：{node_name}。提示模板：{prompt_template or '无'}。"
                    f"优化目标：{optimization_goal}。输出模板：{output_template}。"
                    f"是否需要 explanation：{'是' if include_explanation else '否'}；是否需要 citations：{'是' if include_citations else '否'}。"
                ),
            },
            {
                "role": "system",
                "content": f"知识摘要：\n{knowledge_text}\n历史摘要：\n{history_text}\n业务约束：{constraints or ['无显式约束']}",
            },
            {
                "role": "user",
                "content": (
                    f"问题/事件：{query}\n"
                    f"当前输入：{payload}\n"
                    "请给出结构化决策，并确保 recommended_actions 为数组，每项至少包含 action_type 与 params。"
                    "decision_payload 中必须给出 target_item_id、recommended_quantity、target_dept_id、chat_report、table_write。"
                    "其中 chat_report 至少包含 title、content、audience；table_write 至少包含 item_id、current_stock、safety_limit、recommended_quantity、status。"
                ),
            },
        ]

    @staticmethod
    def _normalize_llm_output(
        *,
        node_name: str,
        raw: dict[str, object],
        fallback: dict[str, JsonValue],
        input_payload: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        decision_payload = raw.get("decision_payload")
        recommended_actions = raw.get("recommended_actions")
        citations = raw.get("citations")
        normalized_payload = DecisionNodeHandler._normalize_decision_payload(
            cast(dict[str, JsonValue], decision_payload) if isinstance(decision_payload, dict) else cast(dict[str, JsonValue], fallback["decision_payload"]),
            input_payload=input_payload,
            fallback_payload=cast(dict[str, JsonValue], fallback["decision_payload"]),
        )
        normalized: dict[str, JsonValue] = {
            "decision_mode": "llm",
            "decision_summary": str(raw.get("decision_summary") or fallback["decision_summary"]),
            "decision_payload": normalized_payload,
            "risk_level": DecisionNodeHandler._normalize_risk_level(raw.get("risk_level"), cast(str, fallback["risk_level"])),
            "recommended_actions": DecisionNodeHandler._normalize_recommended_actions(
                cast(list[JsonValue], recommended_actions) if isinstance(recommended_actions, list) and recommended_actions else cast(list[JsonValue], fallback["recommended_actions"]),
                normalized_payload=normalized_payload,
            ),
            "explanation": str(raw.get("explanation") or f"{node_name} 已基于模型返回生成结构化决策。"),
            "citations": cast(list[JsonValue], citations) if isinstance(citations, list) else cast(list[JsonValue], fallback["citations"]),
        }
        return normalized

    @staticmethod
    def _normalize_risk_level(raw_value: object, fallback: str) -> str:
        if isinstance(raw_value, str) and raw_value in {"low", "medium", "high"}:
            return raw_value
        return fallback

    @staticmethod
    def _number_value(raw_value: object) -> float | None:
        if isinstance(raw_value, (int, float)):
            return float(raw_value)
        if isinstance(raw_value, str):
            try:
                return float(raw_value.strip())
            except ValueError:
                return None
        return None

    @staticmethod
    def _string_value(raw_value: object, *, default: str = "") -> str:
        return raw_value.strip() if isinstance(raw_value, str) and raw_value.strip() else default

    @staticmethod
    def _object_dict(raw_value: object) -> dict[str, object]:
        return cast(dict[str, object], raw_value) if isinstance(raw_value, dict) else {}

    @staticmethod
    def _string_list(raw_value: object, default: list[str]) -> list[str]:
        if isinstance(raw_value, list):
            typed_items = cast(list[object], raw_value)
            values = [item.strip() for item in typed_items if isinstance(item, str) and item.strip()]
            return values or default
        return default

    @staticmethod
    def _float_dict(raw_value: object, default: dict[str, float]) -> dict[str, float]:
        if not isinstance(raw_value, dict):
            return default
        parsed: dict[str, float] = {}
        typed_items = cast(dict[object, object], raw_value)
        for key, value in typed_items.items():
            if not isinstance(key, str) or not key.strip():
                continue
            number = DecisionNodeHandler._number_value(value)
            if number is None:
                continue
            parsed[key.strip()] = number
        return parsed or default

    @staticmethod
    def _resolve_severity(stock_ratio: float | None, thresholds: dict[str, float]) -> str:
        if stock_ratio is None:
            return "medium"
        high_limit = thresholds.get("high", 0.3)
        medium_limit = thresholds.get("medium", 0.8)
        if stock_ratio <= high_limit:
            return "high"
        if stock_ratio <= medium_limit:
            return "medium"
        return "low"

    @staticmethod
    def _model_factor(model_type: str, optimization_goal: str) -> float:
        if model_type == "capacity_planner":
            return 2.2
        if model_type == "risk_balancer":
            return 1.4 if "risk" in optimization_goal else 1.7
        return 1.8 if "timeliness" in optimization_goal else 1.5

    @staticmethod
    def _clamp_quantity(value: int, *, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _score_candidate_actions(
        *,
        candidate_actions: list[str],
        objective_weights: dict[str, float],
        optimization_goal: str,
        demand_pressure: float,
    ) -> tuple[str, dict[str, JsonValue]]:
        scored: dict[str, JsonValue] = {}
        best_action = candidate_actions[0]
        best_score = float("-inf")
        for action in candidate_actions:
            cost_score = 0.9 if "notify" in action else 0.55 if "approval" in action else 0.35
            timeliness_score = 0.95 if "append" in action or "upsert" in action else 0.7 if "approval" in action else 0.45
            stability_score = 0.88 if "approval" in action else 0.62 if "append" in action else 0.52
            score = (
                objective_weights.get("cost", 0.0) * cost_score
                + objective_weights.get("timeliness", 0.0) * timeliness_score * (1 + min(demand_pressure, 1.0) * 0.2)
                + objective_weights.get("stability", 0.0) * stability_score
            )
            if "risk" in optimization_goal and "approval" in action:
                score += 0.08
            if "efficiency" in optimization_goal and ("append" in action or "upsert" in action):
                score += 0.06
            scored[action] = round(score, 4)
            if score > best_score:
                best_score = score
                best_action = action
        return best_action, scored

    @staticmethod
    def _normalize_decision_payload(
        payload: dict[str, JsonValue],
        *,
        input_payload: dict[str, JsonValue],
        fallback_payload: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        target_item_id = DecisionNodeHandler._coalesce_meaningful_value(
            payload.get("target_item_id"),
            input_payload.get("item_id"),
            input_payload.get("target_item_id"),
            fallback_payload.get("target_item_id"),
            default="unknown-item",
        )
        current_stock = DecisionNodeHandler._coalesce_meaningful_value(
            payload.get("current_stock"),
            input_payload.get("stock_count"),
            fallback_payload.get("current_stock"),
        )
        safety_limit = DecisionNodeHandler._coalesce_meaningful_value(
            payload.get("safety_limit"),
            input_payload.get("safety_limit"),
            fallback_payload.get("safety_limit"),
        )
        recommended_quantity = payload.get("recommended_quantity") or fallback_payload.get("recommended_quantity") or 20
        next_step = DecisionNodeHandler._coalesce_meaningful_value(payload.get("next_step"), default="review_and_execute")
        decision_basis = DecisionNodeHandler._coalesce_meaningful_value(
            payload.get("decision_basis"),
            fallback_payload.get("decision_basis"),
            default="llm_structured_reasoning",
        )
        severity = DecisionNodeHandler._coalesce_meaningful_value(payload.get("severity"), fallback_payload.get("severity"), default="medium")
        normalized = dict(payload)
        normalized.update(
            {
                "target_item_id": target_item_id,
                "current_stock": current_stock,
                "safety_limit": safety_limit,
                "recommended_quantity": recommended_quantity,
                "next_step": next_step,
                "decision_basis": decision_basis,
                "severity": severity,
            }
        )
        return DecisionNodeHandler._build_standard_decision_payload(normalized)

    @staticmethod
    def _build_standard_decision_payload(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        normalized = dict(payload)
        target_item_id = DecisionNodeHandler._coalesce_meaningful_value(normalized.get("target_item_id"), default="unknown-item")
        current_stock = normalized.get("current_stock")
        safety_limit = normalized.get("safety_limit")
        recommended_quantity = normalized.get("recommended_quantity") if normalized.get("recommended_quantity") is not None else 20
        target_dept_id = DecisionNodeHandler._coalesce_meaningful_value(
            normalized.get("target_dept_id"),
            normalized.get("dept_id"),
            default="production",
        )
        warehouse_id = DecisionNodeHandler._coalesce_meaningful_value(
            normalized.get("target_warehouse_id"),
            normalized.get("warehouse_id"),
        )
        risk_level = DecisionNodeHandler._coalesce_meaningful_value(
            normalized.get("risk_level"),
            normalized.get("severity"),
            default="medium",
        )

        raw_chat_report = normalized.get("chat_report") if isinstance(normalized.get("chat_report"), dict) else {}
        raw_table_write = normalized.get("table_write") if isinstance(normalized.get("table_write"), dict) else {}

        chat_report: dict[str, JsonValue] = {
            "title": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_chat_report).get("title") if isinstance(raw_chat_report, dict) else None,
                default="库存风险预警",
            ),
            "content": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_chat_report).get("content") if isinstance(raw_chat_report, dict) else None,
                normalized.get("decision_summary"),
                default="检测到库存风险，请及时关注。",
            ),
            "audience": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_chat_report).get("audience") if isinstance(raw_chat_report, dict) else None,
                target_dept_id,
                default="production",
            ),
        }

        table_write: dict[str, JsonValue] = {
            "item_id": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_table_write).get("item_id") if isinstance(raw_table_write, dict) else None,
                target_item_id,
                default="unknown-item",
            ),
            "warehouse_id": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_table_write).get("warehouse_id") if isinstance(raw_table_write, dict) else None,
                warehouse_id,
            ),
            "current_stock": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_table_write).get("current_stock") if isinstance(raw_table_write, dict) else None,
                current_stock,
            ),
            "safety_limit": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_table_write).get("safety_limit") if isinstance(raw_table_write, dict) else None,
                safety_limit,
            ),
            "recommended_quantity": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_table_write).get("recommended_quantity") if isinstance(raw_table_write, dict) else None,
                recommended_quantity,
                default=20,
            ),
            "status": DecisionNodeHandler._coalesce_meaningful_value(
                cast(dict[str, JsonValue], raw_table_write).get("status") if isinstance(raw_table_write, dict) else None,
                default="待处理",
            ),
        }

        normalized.update(
            {
                "target_item_id": target_item_id,
                "recommended_quantity": recommended_quantity,
                "target_dept_id": target_dept_id,
                "target_warehouse_id": warehouse_id,
                "risk_level": risk_level,
                "chat_report": chat_report,
                "table_write": table_write,
            }
        )
        return normalized

    @staticmethod
    def _coalesce_meaningful_value(*values: JsonValue, default: JsonValue | None = None) -> JsonValue:
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip().lower() in {"", "null", "none", "unknown", "unknown-item"}:
                continue
            return value
        return default

    @staticmethod
    def _normalize_recommended_actions(
        actions: list[JsonValue],
        *,
        normalized_payload: dict[str, JsonValue],
    ) -> list[JsonValue]:
        if actions:
            normalized_actions: list[JsonValue] = []
            for item in actions:
                if not isinstance(item, dict):
                    continue
                typed_item = dict(item)
                action_type = typed_item.get("action_type")
                if not isinstance(action_type, str) or not action_type.strip():
                    typed_item["action_type"] = "llm_generated_recommendation"
                params = typed_item.get("params")
                typed_params = dict(params) if isinstance(params, dict) else {}
                _ = typed_params.setdefault("item_id", normalized_payload.get("target_item_id"))
                _ = typed_params.setdefault("quantity", normalized_payload.get("recommended_quantity"))
                typed_item["params"] = cast(JsonValue, typed_params)
                normalized_actions.append(cast(JsonValue, typed_item))
            if normalized_actions:
                return normalized_actions

        return [
            {
                "action_type": "send_risk_report",
                "params": {
                    "target_dept_id": normalized_payload.get("target_dept_id"),
                    "report_key": "chat_report",
                },
            },
            {
                "action_type": "update_replenishment_table",
                "params": {
                    "item_id": normalized_payload.get("target_item_id"),
                    "quantity": normalized_payload.get("recommended_quantity"),
                    "payload_key": "table_write",
                },
            },
        ]
