from __future__ import annotations

from dataclasses import dataclass, field

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | dict[str, "JsonValue"] | list["JsonValue"]


@dataclass(slots=True)
class RuntimeNode:
    id: str
    type: str
    name: str
    config: dict[str, object]


@dataclass(slots=True)
class RuntimeGraph:
    entrypoint: str
    nodes: dict[str, RuntimeNode]
    edges: dict[str, list[str]]


@dataclass(slots=True)
class RuntimeState:
    execution_id: str
    workflow_id: str
    workflow_version: int
    dept_id: str
    current_node: str | None
    input_payload: dict[str, JsonValue] = field(default_factory=dict)
    context: dict[str, JsonValue] = field(default_factory=dict)
    dialog_outputs: dict[str, dict[str, object]] = field(default_factory=dict)
    sensor_outputs: dict[str, dict[str, object]] = field(default_factory=dict)
    decision_outputs: dict[str, dict[str, object]] = field(default_factory=dict)
    tool_outputs: dict[str, dict[str, object]] = field(default_factory=dict)
    history: list[dict[str, JsonValue]] = field(default_factory=list)
    errors: list[dict[str, JsonValue]] = field(default_factory=list)


@dataclass(slots=True)
class NodeExecutionResult:
    next_node_id: str | None = None
    state_updates: dict[str, JsonValue] = field(default_factory=dict)
    route_decided: bool = False
    pause_execution: bool = False
    pause_reason: str | None = None
