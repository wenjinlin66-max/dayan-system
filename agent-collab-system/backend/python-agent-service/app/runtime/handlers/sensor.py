from __future__ import annotations

from typing import cast

from app.domain.memory.service import MemoryService
from app.runtime.models import JsonValue, NodeExecutionResult, RuntimeNode, RuntimeState


class SensorNodeHandler:
    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        memory = MemoryService.bind_runtime(state)
        raw_event = state.input_payload.get("event")
        event_envelope = cast(dict[str, JsonValue], raw_event) if isinstance(raw_event, dict) else {}
        source_payload = self._extract_business_payload(event_envelope, state.input_payload)
        source_matched = self._match_source(node.config, event_envelope)
        condition_matched = self._evaluate_conditions(node.config, source_payload)
        triggered = source_matched and condition_matched
        normalized_payload = self._build_payload(node.config, source_payload, event_envelope)

        sensor_output: dict[str, object] = {
            "source_type": str(node.config.get("source_type") or "manual"),
            "matched": triggered,
            "source_matched": source_matched,
            "condition_matched": condition_matched,
            "triggered": triggered,
            "output_event_name": str(node.config.get("output_event_name") or f"{node.id}.normalized"),
            "payload": normalized_payload,
            "sensor_event": {
                "event_id": event_envelope.get("event_id"),
                "event_type": event_envelope.get("event_type"),
                "source": event_envelope.get("source"),
                "dept_id": event_envelope.get("dept_id"),
            },
            "raw_payload": source_payload if bool(node.config.get("pass_raw_payload")) else None,
        }
        state.sensor_outputs[node.id] = sensor_output
        memory.context.set_context("latest_sensor_node", node.id)
        memory.context.set_context("latest_sensor_event", cast(JsonValue, normalized_payload))
        memory.context.set_context("latest_sensor_triggered", triggered)
        memory.history.write_history(
            {
                "memory_type": "execution_history",
                "agent_type": "sensor_agent",
                "workflow_id": state.workflow_id,
                "execution_id": state.execution_id,
                "summary": f"{node.name} {'命中感知规则' if triggered else '未命中感知规则'}",
                "payload": cast(JsonValue, normalized_payload),
                "matched": triggered,
            }
        )
        return NodeExecutionResult(next_node_id=next_nodes[0] if triggered and next_nodes else None, route_decided=True)

    @staticmethod
    def _build_payload(
        config: dict[str, object],
        source_payload: dict[str, JsonValue],
        event_envelope: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        output_mapping = config.get("output_mapping")
        if isinstance(output_mapping, dict) and output_mapping:
            mapped_payload: dict[str, JsonValue] = {}
            mapping = cast(dict[str, object], output_mapping)
            for key, path in mapping.items():
                if isinstance(path, str):
                    mapped_payload[key] = SensorNodeHandler._resolve_path(source_payload, event_envelope, path)
            return mapped_payload

        selected_fields = config.get("selected_fields")
        if isinstance(selected_fields, list) and selected_fields:
            result: dict[str, JsonValue] = {}
            for field in cast(list[object], selected_fields):
                if isinstance(field, str):
                    result[field] = SensorNodeHandler._resolve_field(source_payload, field)
            return result

        return dict(source_payload)

    @staticmethod
    def _extract_business_payload(
        event_envelope: dict[str, JsonValue],
        input_payload: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        raw_event_payload = event_envelope.get("payload")
        if isinstance(raw_event_payload, dict):
            after_payload = raw_event_payload.get("after")
            if isinstance(after_payload, dict):
                return cast(dict[str, JsonValue], after_payload)
            return cast(dict[str, JsonValue], raw_event_payload)
        return input_payload

    @staticmethod
    def _match_source(config: dict[str, object], event_envelope: dict[str, JsonValue]) -> bool:
        if not event_envelope:
            return str(config.get("source_type") or "manual") in {"manual", "schedule"}

        raw_event_payload = event_envelope.get("payload")
        payload = cast(dict[str, JsonValue], raw_event_payload) if isinstance(raw_event_payload, dict) else {}
        subject = cast(dict[str, JsonValue], event_envelope.get("subject")) if isinstance(event_envelope.get("subject"), dict) else {}

        configured_system = str(config.get("source_system") or "").strip()
        configured_table = str(config.get("source_table") or "").strip()
        configured_event_key = str(config.get("source_event_key") or "").strip()

        source_system = str(payload.get("source_system") or "").strip()
        source_table = str(payload.get("table") or subject.get("record_table_id") or "").strip()
        event_type = str(event_envelope.get("event_type") or "").strip()
        event_key = str(payload.get("event_key") or payload.get("operation") or "").strip()

        if configured_system and not SensorNodeHandler._source_system_matches(configured_system, source_system):
            return False
        if configured_table and configured_table != source_table:
            return False
        if configured_event_key and configured_event_key not in {event_type, event_key}:
            return False
        return True

    @staticmethod
    def _source_system_matches(configured_system: str, source_system: str) -> bool:
        configured = configured_system.strip()
        actual = source_system.strip()
        if configured == actual:
            return True
        aliases = {
            "erp_prod": {"erp_prod", "dayan_mock_records"},
            "dayan_mock_records": {"dayan_mock_records", "erp_prod"},
        }
        return actual in aliases.get(configured, set())

    @staticmethod
    def _evaluate_conditions(config: dict[str, object], source_payload: dict[str, JsonValue]) -> bool:
        raw_conditions = config.get("conditions")
        if not isinstance(raw_conditions, list) or not raw_conditions:
            return True
        results: list[bool] = []
        for item in cast(list[object], raw_conditions):
            if not isinstance(item, dict):
                continue
            condition = cast(dict[str, object], item)
            field = condition.get("field")
            operator = condition.get("operator")
            if not isinstance(field, str) or not isinstance(operator, str):
                continue
            left = SensorNodeHandler._resolve_field(source_payload, field)
            value_from_field = condition.get("value_from_field")
            if isinstance(value_from_field, str):
                right = SensorNodeHandler._resolve_field(source_payload, value_from_field)
            else:
                right = cast(JsonValue, condition.get("value"))
            results.append(SensorNodeHandler._compare(left, operator, right))
        if not results:
            return True
        logic = str(config.get("condition_logic") or "and")
        return any(results) if logic == "or" else all(results)

    @staticmethod
    def _compare(left: JsonValue, operator: str, right: JsonValue) -> bool:
        if operator == "eq":
            return left == right
        if operator == "ne":
            return left != right
        if operator in {">", ">=", "<", "<="} and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if operator == ">":
                return left > right
            if operator == ">=":
                return left >= right
            if operator == "<":
                return left < right
            return left <= right
        return False

    @staticmethod
    def _resolve_field(source_payload: dict[str, JsonValue], path: str) -> JsonValue:
        current: JsonValue = source_payload
        for key in filter(None, path.split(".")):
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    @staticmethod
    def _resolve_path(source_payload: dict[str, JsonValue], event_envelope: dict[str, JsonValue], path: str) -> JsonValue:
        if path.startswith("payload."):
            return SensorNodeHandler._resolve_field(source_payload, path.removeprefix("payload."))
        if path.startswith("event."):
            return SensorNodeHandler._resolve_field(event_envelope, path.removeprefix("event."))
        return SensorNodeHandler._resolve_field(source_payload, path)
