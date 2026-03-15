from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, cast


class WorkflowCompiler:
    """Compile a minimal UI schema into execution DAG."""

    SENSOR_SOURCE_TYPES: ClassVar[set[str]] = {"iot", "form_change", "supply_chain_event", "third_party_notice", "schedule", "manual"}
    SENSOR_OPERATORS: ClassVar[set[str]] = {"eq", "ne", ">", ">=", "<", "<="}
    DECISION_MODES: ClassVar[set[str]] = {"rule", "model", "llm"}
    DECISION_MODEL_TYPES: ClassVar[set[str]] = {"scorecard", "capacity_planner", "risk_balancer"}

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

        outgoing_counts: dict[str, int] = {node_id: 0 for node_id in node_ids}
        for edge in normalized_edges:
            source = edge.get("source")
            if isinstance(source, str) and source in outgoing_counts:
                outgoing_counts[source] += 1

        for node in normalized_nodes:
            node_id = str(node["id"])
            node_type = str(node["type"])
            if node_type in {"sensor_agent", "decision_agent"} and outgoing_counts.get(node_id, 0) == 0:
                errors.append(
                    {
                        "code": "NODE_OUTGOING_EDGE_REQUIRED",
                        "message": f"{node_type} node {node_id} must connect to at least one downstream node",
                    }
                )

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
        if node_type == "decision_agent":
            return self._validate_decision_node(node_id, config)
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

    def _validate_decision_node(self, node_id: str, config: dict[str, object]) -> list[dict[str, str]]:
        errors: list[dict[str, str]] = []
        decision_mode = config.get("decision_mode")
        if not isinstance(decision_mode, str) or decision_mode not in self.DECISION_MODES:
            errors.append(
                {
                    "code": "DECISION_MODE_INVALID",
                    "message": f"decision node {node_id} decision_mode must be one of {', '.join(sorted(self.DECISION_MODES))}",
                }
            )
            return errors

        raw_constraints = config.get("constraints")
        if raw_constraints is not None and (
            not isinstance(raw_constraints, list)
            or any(not isinstance(item, str) or not item.strip() for item in raw_constraints)
        ):
            errors.append(
                {
                    "code": "DECISION_CONSTRAINTS_INVALID",
                    "message": f"decision node {node_id} constraints must be a string array",
                }
            )

        raw_rag_refs = config.get("rag_refs")
        if raw_rag_refs is not None and (
            not isinstance(raw_rag_refs, list)
            or any(not isinstance(item, str) or not item.strip() for item in raw_rag_refs)
        ):
            errors.append(
                {
                    "code": "DECISION_RAG_REFS_INVALID",
                    "message": f"decision node {node_id} rag_refs must be a string array",
                }
            )

        if decision_mode == "rule":
            rule_set_ref = config.get("rule_set_ref")
            rule_config = config.get("rule_config")
            if not (isinstance(rule_set_ref, str) and rule_set_ref.strip()) and not isinstance(rule_config, dict):
                errors.append(
                    {
                        "code": "DECISION_RULE_CONFIG_REQUIRED",
                        "message": f"decision node {node_id} rule mode requires rule_set_ref or rule_config",
                    }
                )
        elif decision_mode == "model":
            model_type = config.get("model_type")
            optimization_goal = config.get("optimization_goal")
            model_params = config.get("model_params")
            if not isinstance(model_type, str) or model_type not in self.DECISION_MODEL_TYPES:
                errors.append(
                    {
                        "code": "DECISION_MODEL_TYPE_INVALID",
                        "message": f"decision node {node_id} model_type must be one of {', '.join(sorted(self.DECISION_MODEL_TYPES))}",
                    }
                )
            if not isinstance(optimization_goal, str) or not optimization_goal.strip():
                errors.append(
                    {
                        "code": "DECISION_OPTIMIZATION_GOAL_REQUIRED",
                        "message": f"decision node {node_id} model mode requires optimization_goal",
                    }
                )
            if model_params is not None and not isinstance(model_params, dict):
                errors.append(
                    {
                        "code": "DECISION_MODEL_PARAMS_INVALID",
                        "message": f"decision node {node_id} model_params must be an object",
                    }
                )
        elif decision_mode == "llm":
            prompt_template = config.get("prompt_template")
            if not isinstance(prompt_template, str) or not prompt_template.strip():
                errors.append(
                    {
                        "code": "DECISION_PROMPT_TEMPLATE_REQUIRED",
                        "message": f"decision node {node_id} llm mode requires prompt_template",
                    }
                )

        for key in ("include_explanation", "include_citations"):
            value = config.get(key)
            if value is not None and not isinstance(value, bool):
                errors.append(
                    {
                        "code": "DECISION_BOOLEAN_FLAG_INVALID",
                        "message": f"decision node {node_id} {key} must be boolean",
                    }
                )

        return errors
