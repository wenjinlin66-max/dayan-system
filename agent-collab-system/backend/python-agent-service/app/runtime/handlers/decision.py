from __future__ import annotations

from typing import cast

from app.domain.memory.service import MemoryService, RuntimeMemoryBundle
from app.runtime.models import JsonValue, NodeExecutionResult, RuntimeNode, RuntimeState


class DecisionNodeHandler:
    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        memory = MemoryService.bind_runtime(state)
        input_values = state.input_payload.get("input_values")
        payload = cast(dict[str, JsonValue], input_values) if isinstance(input_values, dict) else state.input_payload
        decision_mode = str(node.config.get("decision_mode") or "rule")
        decision_output = self._build_decision_output(node, payload, state, decision_mode, memory)
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

    def _build_decision_output(
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
            return self._build_llm_output(node, payload, state, memory)
        return self._build_rule_output(node, payload, state)

    @staticmethod
    def _build_rule_output(node: RuntimeNode, payload: dict[str, JsonValue], state: RuntimeState) -> dict[str, JsonValue]:
        latest_sensor = next(reversed(state.sensor_outputs.values()), None)
        sensor_payload = payload
        if isinstance(latest_sensor, dict):
            raw_sensor_payload = latest_sensor.get("payload")
            if isinstance(raw_sensor_payload, dict):
                sensor_payload = cast(dict[str, JsonValue], raw_sensor_payload)
        base_payload = sensor_payload if sensor_payload else payload
        target_item = base_payload.get("item_id") or base_payload.get("target_item_id") or "unknown-item"
        recommended_quantity = base_payload.get("recommended_quantity") or base_payload.get("quantity") or 100
        return {
            "decision_mode": "rule",
            "decision_summary": f"{node.name} 根据规则判断建议发起执行",
            "decision_payload": {
                "severity": "medium",
                "target_item_id": target_item,
                "recommended_quantity": recommended_quantity,
            },
            "risk_level": "medium",
            "recommended_actions": [
                {
                    "action_type": "create_department_table_record",
                    "params": {
                        "item_id": target_item,
                        "quantity": recommended_quantity,
                    },
                }
            ],
            "explanation": "根据当前输入与感知结果命中规则，生成结构化执行建议。",
            "citations": [],
        }

    @staticmethod
    def _build_model_output(node: RuntimeNode, payload: dict[str, JsonValue], state: RuntimeState) -> dict[str, JsonValue]:
        optimization_goal = str(node.config.get("optimization_goal") or "balance_cost_and_efficiency")
        raw_constraints = node.config.get("constraints")
        constraints: list[object] = cast(list[object], raw_constraints) if isinstance(raw_constraints, list) else []
        target_item = payload.get("item_id") or payload.get("target_item_id") or state.context.get("target_item_id") or "unknown-item"
        return {
            "decision_mode": "model",
            "decision_summary": f"{node.name} 基于模型配置完成一次优化决策",
            "decision_payload": {
                "target_item_id": target_item,
                "optimization_goal": optimization_goal,
                "constraint_count": len(constraints),
                "recommended_quantity": 120,
            },
            "risk_level": "low",
            "recommended_actions": [
                {
                    "action_type": "optimize_replenishment",
                    "params": {
                        "item_id": target_item,
                        "optimization_goal": optimization_goal,
                    },
                }
            ],
            "explanation": "当前为模型型决策骨架，已根据优化目标和约束生成标准化输出。",
            "citations": [],
        }

    @staticmethod
    def _build_llm_output(
        node: RuntimeNode,
        payload: dict[str, JsonValue],
        state: RuntimeState,
        memory: RuntimeMemoryBundle,
    ) -> dict[str, JsonValue]:
        _ = state
        prompt_template = str(node.config.get("prompt_template") or "")
        query = str(payload.get("message") or payload.get("query") or node.name)
        rag_refs_raw = node.config.get("rag_refs")
        rag_refs = [item for item in cast(list[object], rag_refs_raw)] if isinstance(rag_refs_raw, list) else []
        rag_scopes = [item for item in rag_refs if isinstance(item, str)]
        knowledge_hits = memory.knowledge.search_knowledge(query, scopes=rag_scopes)
        history_hits = memory.history.search_history(query, agent_type="decision_agent")
        return {
            "decision_mode": "llm",
            "decision_summary": f"{node.name} 结合知识记忆生成一次智能决策建议",
            "decision_payload": {
                "query": query,
                "prompt_template": prompt_template,
                "knowledge_hit_count": len(knowledge_hits),
                "history_hit_count": len(history_hits),
                "recommended_quantity": 150,
            },
            "risk_level": "medium",
            "recommended_actions": [
                {
                    "action_type": "llm_generated_recommendation",
                    "params": {
                        "query": query,
                    },
                }
            ],
            "explanation": "当前为 LLM 模式骨架：已接入知识/历史记忆检索位点，并输出统一结构。",
            "citations": [
                {
                    "doc_id": str(item.get("doc_id") or ""),
                    "title": str(item.get("title") or "")
                }
                for item in knowledge_hits[:3]
            ],
        }
