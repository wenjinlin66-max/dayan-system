from __future__ import annotations

from typing import cast

from app.runtime.models import RuntimeGraph, RuntimeNode


class GraphBuilder:
    """Build a minimal runtime graph from compiled execution_dag."""

    def build(self, execution_dag: dict[str, object]) -> RuntimeGraph:
        raw_nodes = execution_dag.get("nodes")
        raw_edges = execution_dag.get("edges")
        entrypoint = str(execution_dag.get("entrypoint") or "").strip()

        if not isinstance(raw_nodes, list) or not raw_nodes:
            raise ValueError("RUNTIME_GRAPH_EMPTY")

        nodes: dict[str, RuntimeNode] = {}
        normalized_nodes = cast(list[object], raw_nodes)
        for raw in normalized_nodes:
            if not isinstance(raw, dict):
                continue
            raw_node = cast(dict[str, object], raw)
            node_id = str(raw_node.get("id") or "").strip()
            node_type = str(raw_node.get("type") or "").strip()
            if not node_id or not node_type:
                continue
            raw_config = raw_node.get("config")
            config = cast(dict[str, object], raw_config) if isinstance(raw_config, dict) else {}
            nodes[node_id] = RuntimeNode(
                id=node_id,
                type=node_type,
                name=str(raw_node.get("name") or node_id),
                config={key: value for key, value in config.items()},
            )

        if not nodes:
            raise ValueError("RUNTIME_GRAPH_EMPTY")

        normalized_entrypoint = entrypoint if entrypoint in nodes else next(iter(nodes))
        edges: dict[str, list[str]] = {node_id: [] for node_id in nodes}
        if isinstance(raw_edges, list):
            normalized_edges = cast(list[object], raw_edges)
            for raw in normalized_edges:
                if not isinstance(raw, dict):
                    continue
                raw_edge = cast(dict[str, object], raw)
                source = str(raw_edge.get("source") or "").strip()
                target = str(raw_edge.get("target") or "").strip()
                if source in nodes and target in nodes:
                    edges[source].append(target)

        return RuntimeGraph(entrypoint=normalized_entrypoint, nodes=nodes, edges=edges)
