from __future__ import annotations

from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

from app.db.models.execution import ExecutionCheckpoint, ExecutionRun
from app.domain.approvals.repository import ApprovalRepository
from app.domain.chat.repository import ChatRepository
from app.domain.executions.repository import ExecutionRepository
from app.domain.workflows.repository import WorkflowRepository
from app.integrations.tools.registry import ToolRegistry
from app.runtime.dispatcher import NodeDispatcher, RuntimeHandler
from app.runtime.handlers.approval import ApprovalNodeHandler
from app.runtime.graph_builder import GraphBuilder
from app.runtime.handlers.condition import ConditionNodeHandler
from app.runtime.handlers.decision import DecisionNodeHandler
from app.runtime.handlers.dialog import DialogNodeHandler
from app.runtime.handlers.execution import ExecutionNodeHandler
from app.runtime.handlers.sensor import SensorNodeHandler
from app.runtime.models import JsonValue, RuntimeState
from app.schemas.execution import ExecutionStartRequest, ExecutionStatusResponse


class ExecutionService:
    execution_repository: ExecutionRepository
    workflow_repository: WorkflowRepository
    tool_registry: ToolRegistry
    approval_repository: ApprovalRepository

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        workflow_repository: WorkflowRepository,
        tool_registry: ToolRegistry | None = None,
        approval_repository: ApprovalRepository | None = None,
    ) -> None:
        self.execution_repository = execution_repository
        self.workflow_repository = workflow_repository
        self.tool_registry = tool_registry or ToolRegistry.build_default()
        self.approval_repository = approval_repository or ApprovalRepository(execution_repository.session)

    async def start(
        self,
        payload: ExecutionStartRequest,
        *,
        dept_id: str,
        user_id: str,
    ) -> ExecutionStatusResponse:
        effective_dept_id = payload.dept_id or dept_id
        workflow_version = await self._resolve_workflow_version(payload, dept_id=effective_dept_id)
        execution_id = f"exec_{uuid4().hex[:12]}"
        thread_id = execution_id
        entrypoint = str((workflow_version.execution_dag or {}).get("entrypoint") or "start")
        now = datetime.now(timezone.utc)
        trigger = payload.trigger
        run = ExecutionRun(
            id=execution_id,
            workflow_id=payload.workflow_id,
            workflow_version=workflow_version.version,
            mode=payload.mode,
            thread_id=thread_id,
            entry_node=entrypoint,
            current_node=entrypoint,
            status="running",
            trigger_type=trigger.type,
            dept_id=effective_dept_id,
            started_by=(payload.operator.user_id if payload.operator else user_id),
            trigger_event_id=trigger.event_id,
            correlation_id=trigger.session_id or trigger.message_id,
            context_snapshot={
                "trigger": trigger.model_dump(),
                "input": payload.input,
            },
            final_output=None,
            error_summary=None,
            started_at=now,
            finished_at=None,
        )
        _ = await self.execution_repository.create_run(run)
        checkpoint = ExecutionCheckpoint(
            id=f"chk_{uuid4().hex[:12]}",
            execution_id=execution_id,
            checkpoint_key=f"{execution_id}:{entrypoint}",
            thread_id=thread_id,
            checkpoint_data={"current_node": entrypoint, "input": payload.input},
            current_node=entrypoint,
        )
        _ = await self.execution_repository.create_checkpoint(checkpoint)

        runtime_state = RuntimeState(
            execution_id=execution_id,
            workflow_id=payload.workflow_id,
            workflow_version=workflow_version.version,
            dept_id=effective_dept_id,
            current_node=entrypoint,
            input_payload=self._coerce_json_dict(payload.input),
            context={
                "operator_id": payload.operator.user_id if payload.operator else user_id,
                "trigger_type": trigger.type,
                "chat_session_id": trigger.session_id,
            },
        )

        try:
            if workflow_version.execution_dag:
                paused = False
                if workflow_version.execution_dag:
                    paused = await self._run_execution_graph(workflow_version.execution_dag, runtime_state)
                status_value = "waiting_approval" if paused else "finished"
                await self.execution_repository.update_run(
                    execution_id,
                    current_node=runtime_state.current_node,
                    status=status_value,
                    final_output=self._build_final_output(runtime_state),
                    finished_at=None if paused else datetime.now(timezone.utc),
                    context_snapshot={
                        "trigger": trigger.model_dump(),
                        "input": payload.input,
                        "history": runtime_state.history,
                        "approval_title": runtime_state.context.get("approval_title"),
                        "approval_summary": runtime_state.context.get("approval_summary"),
                        "approval_current_node": runtime_state.context.get("approval_current_node"),
                        "approval_next_node": runtime_state.context.get("approval_next_node"),
                    },
                )
                if not paused:
                    await self._append_execution_message(
                        session_id=trigger.session_id,
                        dept_id=effective_dept_id,
                        execution_id=execution_id,
                        workflow_id=payload.workflow_id,
                        status=status_value,
                        current_node=runtime_state.current_node,
                    )
        except ValueError as exc:
            await self.execution_repository.update_run(
                execution_id,
                current_node=runtime_state.current_node,
                status="failed",
                error_summary=str(exc),
                final_output=self._build_final_output(runtime_state),
                finished_at=datetime.now(timezone.utc),
            )
            await self._append_execution_message(
                session_id=trigger.session_id,
                dept_id=effective_dept_id,
                execution_id=execution_id,
                workflow_id=payload.workflow_id,
                status="failed",
                current_node=runtime_state.current_node,
                error_summary=str(exc),
            )
        await self.execution_repository.session.commit()
        latest_run = await self.execution_repository.get_run(execution_id)
        if latest_run is None:
            raise ValueError("EXECUTION_NOT_FOUND")
        return self._to_response(latest_run)

    async def get_status(self, execution_id: str) -> ExecutionStatusResponse:
        run = await self.execution_repository.get_run(execution_id)
        if run is None:
            raise ValueError("EXECUTION_NOT_FOUND")
        return self._to_response(run)

    async def get_status_for_dept(self, execution_id: str, *, dept_id: str) -> ExecutionStatusResponse:
        run = await self.execution_repository.get_run(execution_id)
        if run is None or run.dept_id != dept_id:
            raise ValueError("EXECUTION_NOT_FOUND")
        return self._to_response(run)

    async def resume_from_approval(
        self,
        execution_id: str,
        *,
        next_node: str | None,
        decision: str,
        comment: str | None,
    ) -> ExecutionStatusResponse:
        run = await self.execution_repository.get_run(execution_id)
        if run is None:
            raise ValueError("EXECUTION_NOT_FOUND")

        if decision != "approved":
            await self.execution_repository.update_run(
                execution_id,
                status="cancelled",
                error_summary=comment or "审批驳回",
                finished_at=datetime.now(timezone.utc),
            )
            await self._append_execution_message(
                session_id=self._extract_session_id(run),
                dept_id=run.dept_id,
                execution_id=execution_id,
                workflow_id=run.workflow_id,
                status="cancelled",
                current_node=run.current_node,
                error_summary=comment or "审批驳回",
            )
            await self.execution_repository.session.commit()
            updated = await self.execution_repository.get_run(execution_id)
            if updated is None:
                raise ValueError("EXECUTION_NOT_FOUND")
            return self._to_response(updated)

        workflow_version = await self._get_workflow_version(run.workflow_id, run.workflow_version, run.mode)
        context_input = self._extract_nested_dict(run.context_snapshot, "input")
        final_context = self._extract_nested_dict(run.final_output, "context")
        runtime_state = RuntimeState(
            execution_id=run.id,
            workflow_id=run.workflow_id,
            workflow_version=run.workflow_version,
            dept_id=run.dept_id,
            current_node=next_node,
            input_payload=self._coerce_json_dict(context_input),
            context=self._coerce_json_dict(final_context),
        )
        runtime_state.context["approval_decision"] = decision
        runtime_state.context["approval_comment"] = comment
        paused = False
        if workflow_version.execution_dag:
            paused = await self._run_execution_graph(workflow_version.execution_dag, runtime_state, start_node=next_node)
        await self.execution_repository.update_run(
            execution_id,
            current_node=runtime_state.current_node,
            status="waiting_approval" if paused else "finished",
            final_output=self._build_final_output(runtime_state),
            finished_at=None if paused else datetime.now(timezone.utc),
        )
        if not paused:
            await self._append_execution_message(
                session_id=self._extract_session_id(run),
                dept_id=run.dept_id,
                execution_id=execution_id,
                workflow_id=run.workflow_id,
                status="finished",
                current_node=runtime_state.current_node,
            )
        await self.execution_repository.session.commit()
        updated = await self.execution_repository.get_run(execution_id)
        if updated is None:
            raise ValueError("EXECUTION_NOT_FOUND")
        return self._to_response(updated)

    async def _run_execution_graph(self, execution_dag: dict[str, object], state: RuntimeState, start_node: str | None = None) -> bool:
        graph = GraphBuilder().build(execution_dag)
        dispatcher = self._build_dispatcher(self.tool_registry, self.approval_repository)
        current_node_id = start_node or graph.entrypoint
        visited = 0

        while current_node_id:
            visited += 1
            if visited > max(len(graph.nodes) * 2, 20):
                raise ValueError("EXECUTION_GRAPH_GUARD_TRIGGERED")

            node = graph.nodes.get(current_node_id)
            if node is None:
                raise ValueError("EXECUTION_NODE_NOT_FOUND")

            state.current_node = current_node_id
            handler = dispatcher.get_handler(node.type)
            if handler is None:
                raise ValueError(f"HANDLER_NOT_IMPLEMENTED:{node.type}")

            next_nodes = graph.edges.get(current_node_id, [])
            result = await handler.execute(node, state, next_nodes)
            state.history.append(
                {
                    "node_id": node.id,
                    "node_type": node.type,
                    "next_node": result.next_node_id,
                }
            )
            checkpoint = ExecutionCheckpoint(
                id=f"chk_{uuid4().hex[:12]}",
                execution_id=state.execution_id,
                checkpoint_key=f"{state.execution_id}:{visited}:{node.id}",
                thread_id=state.execution_id,
                checkpoint_data={
                    "current_node": node.id,
                    "history": state.history,
                    "sensor_outputs": state.sensor_outputs,
                    "tool_outputs": state.tool_outputs,
                    "decision_outputs": state.decision_outputs,
                },
                current_node=node.id,
            )
            _ = await self.execution_repository.create_checkpoint(checkpoint)
            if result.pause_execution:
                return True
            current_node_id = result.next_node_id if result.route_decided else (result.next_node_id or (next_nodes[0] if next_nodes else None))
        return False

    @staticmethod
    def _build_dispatcher(tool_registry: ToolRegistry, approval_repository: ApprovalRepository) -> NodeDispatcher:
        handlers: dict[str, RuntimeHandler] = {
                "dialog_agent": DialogNodeHandler(),
                "sensor_agent": SensorNodeHandler(),
                "decision_agent": DecisionNodeHandler(),
                "condition": ConditionNodeHandler(),
                "approval": ApprovalNodeHandler(approval_repository),
                "execution_agent": ExecutionNodeHandler(tool_registry.get_department_table_writer()),
            }
        return NodeDispatcher(handlers)

    async def _get_workflow_version(self, workflow_id: str, version: int, mode: str):
        resolved = await self.workflow_repository.get_version(workflow_id, version)
        if resolved is None:
            raise ValueError("WORKFLOW_VERSION_NOT_FOUND")
        if mode == "released" and resolved.mode != "released":
            raise ValueError("RELEASE_NOT_FOUND")
        return resolved

    @staticmethod
    def _build_final_output(state: RuntimeState) -> dict[str, JsonValue]:
        return {
            "history": cast(list[JsonValue], state.history),
            "context": state.context,
            "sensor_outputs": cast(dict[str, JsonValue], state.sensor_outputs),
            "decision_outputs": cast(dict[str, JsonValue], state.decision_outputs),
            "tool_outputs": cast(dict[str, JsonValue], state.tool_outputs),
            "errors": cast(list[JsonValue], state.errors),
        }

    @staticmethod
    def _coerce_json_dict(payload: dict[str, object]) -> dict[str, JsonValue]:
        return {key: cast(JsonValue, value) for key, value in payload.items()}

    @staticmethod
    def _extract_nested_dict(payload: dict[str, object] | None, key: str) -> dict[str, object]:
        if not isinstance(payload, dict):
            return {}
        value = payload.get(key)
        return cast(dict[str, object], value) if isinstance(value, dict) else {}

    async def _resolve_workflow_version(self, payload: ExecutionStartRequest, *, dept_id: str):
        workflow = await self.workflow_repository.get_workflow(payload.workflow_id)
        if workflow is None or workflow.owner_dept_id != dept_id:
            raise ValueError("WORKFLOW_VERSION_NOT_FOUND")
        if payload.version is not None:
            version = await self.workflow_repository.get_version(payload.workflow_id, payload.version)
            if version is None:
                raise ValueError("WORKFLOW_VERSION_NOT_FOUND")
            if version.compile_status != "success" or version.execution_dag is None:
                raise ValueError("WORKFLOW_NOT_COMPILED")
            return version
        current = await self.workflow_repository.get_current_release(payload.workflow_id)
        if current is None:
            raise ValueError("RELEASE_NOT_FOUND")
        if current.compile_status != "success" or current.execution_dag is None:
            raise ValueError("WORKFLOW_NOT_COMPILED")
        return current

    @staticmethod
    def _extract_session_id(run: ExecutionRun) -> str | None:
        snapshot = run.context_snapshot if isinstance(run.context_snapshot, dict) else {}
        trigger = snapshot.get("trigger")
        if isinstance(trigger, dict):
            session_id = trigger.get("session_id")
            if isinstance(session_id, str) and session_id:
                return session_id
        return run.correlation_id if isinstance(run.correlation_id, str) and run.correlation_id.startswith("chat_") else None

    async def _append_execution_message(
        self,
        *,
        session_id: str | None,
        dept_id: str,
        execution_id: str,
        workflow_id: str,
        status: str,
        current_node: str | None,
        error_summary: str | None = None,
    ) -> None:
        if not session_id:
            return
        repository = ChatRepository(self.execution_repository.session)
        content = (
            f"部门对话框收到执行结果：workflow={workflow_id}，status={status}，当前节点={current_node or '-'}。"
            if not error_summary
            else f"部门对话框收到执行结果：workflow={workflow_id}，status={status}，原因={error_summary}。"
        )
        await repository.append_assistant_message(
            session_id=session_id,
            dept_id=dept_id,
            content=content,
            payload={
                "message_kind": "execution_result",
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": status,
                "current_node": current_node,
                "error_summary": error_summary,
            },
            related_execution_id=execution_id,
        )

    @staticmethod
    def _to_response(run: ExecutionRun) -> ExecutionStatusResponse:
        updated_at = run.finished_at or run.started_at
        return ExecutionStatusResponse(
            execution_id=run.id,
            workflow_id=run.workflow_id,
            workflow_version=run.workflow_version,
            mode=run.mode,
            status=run.status,
            current_node=run.current_node,
            thread_id=run.thread_id,
            dept_id=run.dept_id,
            started_at=run.started_at.isoformat() if run.started_at else None,
            updated_at=updated_at.isoformat() if updated_at else None,
            final_output=run.final_output,
        )
