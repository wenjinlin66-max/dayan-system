from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast


class WorkflowCompiler:
    """Compile a minimal UI schema into execution DAG."""

    SENSOR_SOURCE_TYPES: ClassVar[set[str]] = {"iot", "form_change", "supply_chain_event", "third_party_notice", "schedule", "manual"}
    SENSOR_OPERATORS: ClassVar[set[str]] = {"eq", "ne", ">", ">=", "<", "<="}

    def compile(self, ui_schema: dict[str, object]) -> tuple[dict[str, object], list[dict[str, str]]]:
        nodes = self._as_sequence(ui_schema.get("nodes"))
        edges = self._as_sequence(ui_schema.get("edges"))

        if not nodes:
            return {"entrypoint": None, "nodes": [], "edges": []}, [
                {"code": "EMPTY_WORKFLOW", "message": "workflow must contain at least one node"}
            ]

        normalized_nodes: list[dict[str, object]] = []
        node_ids: set[str] = set()
        incoming: set[str] = set()
        normalized_edges: list[dict[str, object]] = []
        errors: list[dict[str, str]] = []

        for raw in nodes:
            if not isinstance(raw, dict):
                errors.append({"code": "INVALID_NODE", "message": "node must be an object"})
                continue
            node_id = str(raw.get("id") or "").strip()
            node_type = str(raw.get("type") or "").strip()
            if not node_id or not node_type:
                errors.append({"code": "INVALID_NODE", "message": "node id and type are required"})
                continue
            raw_config = raw.get("config") or raw.get("data") or {}
            config = cast(dict[str, object], raw_config)
            if not isinstance(config, dict):
                errors.append({"code": "INVALID_NODE_CONFIG", "message": f"node {node_id} config must be an object"})
                continue
            node_ids.add(node_id)
            normalized_nodes.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "name": raw.get("label") or raw.get("name") or node_id,
                    "config": config,
                    "runtime": raw.get("runtime") or {},
                }
            )
            errors.extend(self._validate_node(node_id, node_type, config))

        for raw in edges:
            if not isinstance(raw, dict):
                errors.append({"code": "INVALID_EDGE", "message": "edge must be an object"})
                continue
            source = str(raw.get("source") or "").strip()
            target = str(raw.get("target") or "").strip()
            if not source or not target:
                errors.append({"code": "INVALID_EDGE", "message": "edge source and target are required"})
                continue
            if source not in node_ids or target not in node_ids:
                errors.append({"code": "EDGE_NODE_NOT_FOUND", "message": f"edge {source}->{target} references unknown node"})
                continue
            incoming.add(target)
            normalized_edges.append({"source": source, "target": target, "label": raw.get("label")})

        if errors:
            return {"entrypoint": None, "nodes": normalized_nodes, "edges": normalized_edges}, errors

        entrypoint = next((node["id"] for node in normalized_nodes if node["id"] not in incoming), normalized_nodes[0]["id"])
        return {"entrypoint": entrypoint, "nodes": normalized_nodes, "edges": normalized_edges}, []

    @staticmethod
    def _as_sequence(value: object) -> Sequence[object]:
        if isinstance(value, list):
            return value
        return []

    def _validate_node(self, node_id: str, node_type: str, config: dict[str, object]) -> list[dict[str, str]]:
        if node_type != "sensor_agent":
            return []

        errors: list[dict[str, str]] = []
        source_type = config.get("source_type")
        if source_type is not None and source_type not in self.SENSOR_SOURCE_TYPES:
            errors.append(
                {
                    "code": "SENSOR_SOURCE_TYPE_INVALID",
                    "message": f"sensor node {node_id} source_type must be one of {', '.join(sorted(self.SENSOR_SOURCE_TYPES))}",
                }
            )

        raw_logic = config.get("condition_logic")
        if raw_logic is not None and raw_logic not in {"and", "or"}:
            errors.append(
                {
                    "code": "SENSOR_CONDITION_LOGIC_INVALID",
                    "message": f"sensor node {node_id} condition_logic must be and/or",
                }
            )

        raw_conditions = config.get("conditions")
        if raw_conditions is not None:
            if not isinstance(raw_conditions, list):
                errors.append(
                    {
                        "code": "SENSOR_CONDITIONS_INVALID",
                        "message": f"sensor node {node_id} conditions must be a list",
                    }
                )
            else:
                for index, item in enumerate(raw_conditions, start=1):
                    if not isinstance(item, dict):
                        errors.append(
                            {
                                "code": "SENSOR_CONDITION_INVALID",
                                "message": f"sensor node {node_id} condition #{index} must be an object",
                            }
                        )
                        continue
                    field = item.get("field")
                    operator = item.get("operator")
                    if not isinstance(field, str) or not field.strip():
                        errors.append(
                            {
                                "code": "SENSOR_CONDITION_FIELD_REQUIRED",
                                "message": f"sensor node {node_id} condition #{index} field is required",
                            }
                        )
                    if not isinstance(operator, str) or operator not in self.SENSOR_OPERATORS:
                        errors.append(
                            {
                                "code": "SENSOR_CONDITION_OPERATOR_INVALID",
                                "message": f"sensor node {node_id} condition #{index} operator is invalid",
                            }
                        )

        raw_mapping = config.get("output_mapping")
        if raw_mapping is not None:
            if not isinstance(raw_mapping, dict):
                errors.append(
                    {
                        "code": "SENSOR_OUTPUT_MAPPING_INVALID",
                        "message": f"sensor node {node_id} output_mapping must be an object",
                    }
                )
            else:
                for key, value in raw_mapping.items():
                    if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
                        errors.append(
                            {
                                "code": "SENSOR_OUTPUT_MAPPING_ENTRY_INVALID",
                                "message": f"sensor node {node_id} output_mapping entries must be non-empty string pairs",
                            }
                        )
                        break

        raw_selected_fields = config.get("selected_fields")
        if raw_selected_fields is not None:
            selected_fields = cast(list[object], raw_selected_fields) if isinstance(raw_selected_fields, list) else None
            if selected_fields is None or any(not isinstance(item, str) or not item.strip() for item in selected_fields):
                errors.append(
                    {
                        "code": "SENSOR_SELECTED_FIELDS_INVALID",
                        "message": f"sensor node {node_id} selected_fields must be a string array",
                    }
                )

        return errors
