from __future__ import annotations

import json

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

from app.db.models.workflow import Workflow, WorkflowRegistry, WorkflowVersion
from app.domain.workflows.compiler import WorkflowCompiler
from app.domain.workflows.repository import WorkflowRepository
from app.domain.workflows.service import WorkflowService
from app.schemas.workflow import WorkflowCompileRequest, WorkflowCreateRequest, WorkflowDraftUpdateRequest, WorkflowPublishRequest


SYSTEM_USER_ID = "system_seed"
LEGACY_SENSOR_TABLES = {"inventory_stock", "production_order", "device_status"}


WORKFLOW_SPECS: tuple[dict[str, object], ...] = (
    {
        "code": "parts-demand-purchase-fanout",
        "name": "零件需求下发-采购表单",
        "owner_dept_id": "supply_chain",
        "summary": "当零件需求表新增采购类零件时，自动下发到采购表单。",
        "release_note": "seed purchase request fan-out workflow",
        "source_type": "purchase",
        "target_ref": "purchase_request",
        "default_values": {
            "supplier_hint": "待采购/销售确认供应来源",
            "request_status": "pending",
        },
        "record_key_template": "{{sensor_payload.order_no}}:{{sensor_payload.part_code}}:purchase",
        "row_mapping": {
            "order_no": "sensor_payload.order_no",
            "product_code": "sensor_payload.product_code",
            "part_code": "sensor_payload.part_code",
            "part_name": "sensor_payload.part_name",
            "request_qty": "sensor_payload.purchase_qty",
            "estimated_cost": "sensor_payload.total_cost",
        },
    },
    {
        "code": "parts-demand-manufacturing-fanout",
        "name": "零件需求下发-生产表单",
        "owner_dept_id": "production",
        "summary": "当零件需求表新增生产类零件时，自动下发到生产表单。",
        "release_note": "seed manufacturing request fan-out workflow",
        "source_type": "manufacture",
        "target_ref": "manufacturing_request",
        "default_values": {
            "workshop_id": "WS-ASM",
            "request_status": "pending",
        },
        "record_key_template": "{{sensor_payload.order_no}}:{{sensor_payload.part_code}}:manufacture",
        "row_mapping": {
            "order_no": "sensor_payload.order_no",
            "product_code": "sensor_payload.product_code",
            "part_code": "sensor_payload.part_code",
            "part_name": "sensor_payload.part_name",
            "request_qty": "sensor_payload.manufacture_qty",
            "estimated_cost": "sensor_payload.total_cost",
        },
    },
    {
        "code": "parts-demand-customer-fanout",
        "name": "零件需求下发-客户配合表单",
        "owner_dept_id": "supply_chain",
        "summary": "当零件需求表新增客户提供类零件时，自动下发到客户配合表单，并由采购/供应链侧统筹跟进。",
        "release_note": "seed customer supply request fan-out workflow",
        "source_type": "customer",
        "target_ref": "customer_supply_request",
        "default_values": {
            "handoff_note": "等待客户备料/随货提供",
            "request_status": "pending",
        },
        "record_key_template": "{{sensor_payload.order_no}}:{{sensor_payload.part_code}}:customer",
        "row_mapping": {
            "order_no": "sensor_payload.order_no",
            "customer_name": "sensor_payload.customer_name",
            "product_code": "sensor_payload.product_code",
            "part_code": "sensor_payload.part_code",
            "part_name": "sensor_payload.part_name",
            "request_qty": "sensor_payload.customer_qty",
        },
    },
)


DIALOG_ORDER_WORKFLOW_SPEC: dict[str, object] = {
    "code": "dialog-sales-order-intake",
    "name": "对话录入销售订单",
    "owner_dept_id": "supply_chain",
    "summary": "用户在对话框发送销售订单文本后，系统自动识别订单字段，缺少字段时追问补齐，最终写入客户订单表。",
    "release_note": "seed dialog sales order intake workflow",
    "synonyms": ["销售订单", "客户下单", "录入订单", "登记订单"],
    "example_utterances": [
        "客户果链A下单 10 台苹果手机 demo 款，帮我录入订单",
        "帮我登记销售订单，订单号 SO-20260321-010，客户果链B，PHONE-001，数量 20",
    ],
    "required_inputs": ["order_no", "customer_name", "product_code", "product_name", "ordered_qty", "unit_price"],
    "input_schema": {
        "properties": {
            "order_no": {"title": "订单号", "type": "string", "placeholder": "例如 SO-20260321-010"},
            "customer_name": {"title": "客户名称", "type": "string", "placeholder": "例如 果链客户A"},
            "product_code": {"title": "产品编码", "type": "string", "placeholder": "例如 PHONE-001"},
            "product_name": {"title": "产品名称", "type": "string", "placeholder": "例如 苹果手机 demo 款"},
            "ordered_qty": {"title": "订单数量", "type": "integer", "placeholder": "例如 10"},
            "unit_price": {"title": "单价", "type": "number", "placeholder": "例如 6999"},
            "order_status": {"title": "订单状态", "type": "string", "placeholder": "默认 draft"},
        }
    },
}


ORDER_PROJECTION_WORKFLOW_SPEC: dict[str, object] = {
    "code": "customer-order-parts-demand-projection",
    "name": "客户订单拆解零件需求",
    "owner_dept_id": "supply_chain",
    "summary": "当客户订单新增或更新时，调用决策型智能体按产品 BOM 拆解零件需求并重建 parts_demand。",
    "release_note": "seed customer order to parts demand projection workflow",
}


async def seed_parts_demand_workflows(session: AsyncSession) -> None:
    repository = WorkflowRepository(session)
    service = WorkflowService(repository, WorkflowCompiler())

    for spec in WORKFLOW_SPECS:
        workflow = await _get_workflow_by_code(session, str(spec["code"]))
        desired_ui_schema = _build_parts_demand_ui_schema(spec)

        if workflow is None:
            created = await service.create_workflow(
                WorkflowCreateRequest(
                    name=str(spec["name"]),
                    code=str(spec["code"]),
                    visibility="private",
                    owner_dept_id=str(spec["owner_dept_id"]),
                    ui_schema=desired_ui_schema,
                ),
                dept_id=str(spec["owner_dept_id"]),
                user_id=SYSTEM_USER_ID,
            )
            workflow = await repository.get_workflow(created.workflow_id)

        if workflow is None:
            continue

        if workflow.owner_dept_id != str(spec["owner_dept_id"]) or workflow.name != str(spec["name"]):
            await repository.update_workflow(
                workflow.id,
                owner_dept_id=str(spec["owner_dept_id"]),
                name=str(spec["name"]),
                updated_by=SYSTEM_USER_ID,
            )
            await repository.session.commit()
            workflow = await repository.get_workflow(workflow.id)
            if workflow is None:
                continue

        current_release = await repository.get_current_release(workflow.id)
        if current_release is not None and current_release.ui_schema == desired_ui_schema and current_release.compile_status == "success":
            await _ensure_synced_draft(service, repository, workflow, desired_ui_schema)
            continue

        _ = await service.update_draft(
            workflow.id,
            WorkflowDraftUpdateRequest(name=str(spec["name"]), ui_schema=desired_ui_schema, schema_version="2026-03"),
            dept_id=workflow.owner_dept_id,
            user_id=SYSTEM_USER_ID,
        )
        _ = await service.compile_workflow(
            workflow.id,
            WorkflowCompileRequest(schema_version="2026-03"),
            dept_id=workflow.owner_dept_id,
        )
        _ = await service.publish_workflow(
            workflow.id,
            WorkflowPublishRequest(
                release_note=str(spec["release_note"]),
                category="event_trigger",
                summary=str(spec["summary"]),
            ),
            dept_id=workflow.owner_dept_id,
        )
        workflow = await repository.get_workflow(workflow.id)
        if workflow is not None:
            await _ensure_synced_draft(service, repository, workflow, desired_ui_schema)


async def seed_dialog_order_workflow(session: AsyncSession) -> None:
    repository = WorkflowRepository(session)
    service = WorkflowService(repository, WorkflowCompiler())
    spec = DIALOG_ORDER_WORKFLOW_SPEC
    desired_ui_schema = _build_dialog_order_ui_schema(spec)
    workflow = await _get_workflow_by_code(session, str(spec["code"]))

    if workflow is None:
        created = await service.create_workflow(
            WorkflowCreateRequest(
                name=str(spec["name"]),
                code=str(spec["code"]),
                visibility="private",
                owner_dept_id=str(spec["owner_dept_id"]),
                ui_schema=desired_ui_schema,
            ),
            dept_id=str(spec["owner_dept_id"]),
            user_id=SYSTEM_USER_ID,
        )
        workflow = await repository.get_workflow(created.workflow_id)

    if workflow is None:
        return

    if workflow.owner_dept_id != str(spec["owner_dept_id"]) or workflow.name != str(spec["name"]):
        await repository.update_workflow(
            workflow.id,
            owner_dept_id=str(spec["owner_dept_id"]),
            name=str(spec["name"]),
            updated_by=SYSTEM_USER_ID,
        )
        await repository.session.commit()
        workflow = await repository.get_workflow(workflow.id)
        if workflow is None:
            return

    current_release = await repository.get_current_release(workflow.id)
    if current_release is not None and current_release.ui_schema == desired_ui_schema and current_release.compile_status == "success":
        await _ensure_synced_draft(service, repository, workflow, desired_ui_schema)
        return

    _ = await service.update_draft(
        workflow.id,
        WorkflowDraftUpdateRequest(name=str(spec["name"]), ui_schema=desired_ui_schema, schema_version="2026-03"),
        dept_id=workflow.owner_dept_id,
        user_id=SYSTEM_USER_ID,
    )
    _ = await service.compile_workflow(
        workflow.id,
        WorkflowCompileRequest(schema_version="2026-03"),
        dept_id=workflow.owner_dept_id,
    )
    _ = await service.publish_workflow(
        workflow.id,
        WorkflowPublishRequest(
            release_note=str(spec["release_note"]),
            category="dialog_trigger",
            summary=str(spec["summary"]),
        ),
        dept_id=workflow.owner_dept_id,
    )
    workflow = await repository.get_workflow(workflow.id)
    if workflow is not None:
        await _ensure_synced_draft(service, repository, workflow, desired_ui_schema)


async def seed_order_projection_workflow(session: AsyncSession) -> None:
    repository = WorkflowRepository(session)
    service = WorkflowService(repository, WorkflowCompiler())
    spec = ORDER_PROJECTION_WORKFLOW_SPEC
    desired_ui_schema = _build_order_projection_ui_schema(spec)
    workflow = await _get_workflow_by_code(session, str(spec["code"]))

    if workflow is None:
        created = await service.create_workflow(
            WorkflowCreateRequest(
                name=str(spec["name"]),
                code=str(spec["code"]),
                visibility="private",
                owner_dept_id=str(spec["owner_dept_id"]),
                ui_schema=desired_ui_schema,
            ),
            dept_id=str(spec["owner_dept_id"]),
            user_id=SYSTEM_USER_ID,
        )
        workflow = await repository.get_workflow(created.workflow_id)

    if workflow is None:
        return

    if workflow.owner_dept_id != str(spec["owner_dept_id"]) or workflow.name != str(spec["name"]):
        await repository.update_workflow(
            workflow.id,
            owner_dept_id=str(spec["owner_dept_id"]),
            name=str(spec["name"]),
            updated_by=SYSTEM_USER_ID,
        )
        await repository.session.commit()
        workflow = await repository.get_workflow(workflow.id)
        if workflow is None:
            return

    current_release = await repository.get_current_release(workflow.id)
    if current_release is not None and current_release.ui_schema == desired_ui_schema and current_release.compile_status == "success":
        await _ensure_synced_draft(service, repository, workflow, desired_ui_schema)
        return

    _ = await service.update_draft(
        workflow.id,
        WorkflowDraftUpdateRequest(name=str(spec["name"]), ui_schema=desired_ui_schema, schema_version="2026-03"),
        dept_id=workflow.owner_dept_id,
        user_id=SYSTEM_USER_ID,
    )
    _ = await service.compile_workflow(
        workflow.id,
        WorkflowCompileRequest(schema_version="2026-03"),
        dept_id=workflow.owner_dept_id,
    )
    _ = await service.publish_workflow(
        workflow.id,
        WorkflowPublishRequest(
            release_note=str(spec["release_note"]),
            category="event_trigger",
            summary=str(spec["summary"]),
        ),
        dept_id=workflow.owner_dept_id,
    )
    workflow = await repository.get_workflow(workflow.id)
    if workflow is not None:
        await _ensure_synced_draft(service, repository, workflow, desired_ui_schema)


async def cleanup_legacy_workflow_artifacts(session: AsyncSession) -> None:
    repository = WorkflowRepository(session)
    protected_codes = {*(str(spec["code"]) for spec in WORKFLOW_SPECS), str(DIALOG_ORDER_WORKFLOW_SPEC["code"])}
    protected_codes.add(str(ORDER_PROJECTION_WORKFLOW_SPEC["code"]))
    workflows = await repository.list_workflows()

    for workflow in workflows:
        versions = await repository.list_versions(workflow.id)
        legacy_versions = [version for version in versions if _version_uses_legacy_sensor_table(version)]
        if not legacy_versions:
            continue

        if workflow.code not in protected_codes:
            current_release = await repository.get_current_release(workflow.id)
            latest_draft = await repository.get_latest_draft(workflow.id)
            if (
                (current_release is not None and _version_uses_legacy_sensor_table(current_release))
                or (latest_draft is not None and _version_uses_legacy_sensor_table(latest_draft))
            ):
                await repository.delete_registry_entries(workflow.id)
                await repository.delete_versions(workflow.id)
                await repository.delete_workflow_row(workflow.id)
                continue

        removable_version_ids = [version.id for version in legacy_versions if not version.is_current_release and version.mode != "draft"]
        if removable_version_ids:
            await session.execute(delete(WorkflowRegistry).where(WorkflowRegistry.workflow_id == workflow.id, WorkflowRegistry.workflow_version.in_([version.version for version in legacy_versions if version.id in removable_version_ids])))
            await session.execute(delete(WorkflowVersion).where(WorkflowVersion.id.in_(removable_version_ids)))

    await session.commit()


async def _get_workflow_by_code(session: AsyncSession, code: str) -> Workflow | None:
    result = await session.execute(select(Workflow).where(Workflow.code == code, Workflow.status == "active"))
    return result.scalar_one_or_none()


async def _ensure_synced_draft(
    service: WorkflowService,
    repository: WorkflowRepository,
    workflow: Workflow,
    desired_ui_schema: dict[str, object],
) -> None:
    latest_draft = await repository.get_latest_draft(workflow.id)
    if latest_draft is not None and latest_draft.ui_schema == desired_ui_schema:
        return
    _ = await service.update_draft(
        workflow.id,
        WorkflowDraftUpdateRequest(name=workflow.name, ui_schema=desired_ui_schema, schema_version="2026-03"),
        dept_id=workflow.owner_dept_id,
        user_id=SYSTEM_USER_ID,
    )


def _version_uses_legacy_sensor_table(version: WorkflowVersion) -> bool:
    ui_schema = version.ui_schema if isinstance(version.ui_schema, dict) else {}
    raw_nodes = ui_schema.get("nodes") if isinstance(ui_schema, dict) else None
    if not isinstance(raw_nodes, list):
        return False
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict) or raw_node.get("type") != "sensor_agent":
            continue
        config = raw_node.get("config")
        if not isinstance(config, dict):
            continue
        if config.get("source_table") in LEGACY_SENSOR_TABLES:
            return True
    return False


def _build_parts_demand_ui_schema(spec: dict[str, object]) -> dict[str, object]:
    source_type = str(spec["source_type"])
    target_ref = str(spec["target_ref"])
    row_mapping = json.loads(json.dumps(spec["row_mapping"], ensure_ascii=False))
    default_values = json.loads(json.dumps(spec["default_values"], ensure_ascii=False))
    workflow_code = str(spec["code"])

    return {
        "nodes": [
            {
                "id": "sensor_parts_demand",
                "type": "sensor_agent",
                "label": "需求表感知",
                "config": {
                    "source_type": "form_change",
                    "source_system": "erp_prod",
                    "source_table": "parts_demand",
                    "source_event_key": "record.created",
                    "condition_logic": "and",
                    "conditions": [
                        {
                            "field": "source_type",
                            "operator": "eq",
                            "value": source_type,
                        }
                    ],
                },
            },
            {
                "id": "execution_fanout",
                "type": "execution_agent",
                "label": "部门表单下发",
                "config": {
                    "approval_required": False,
                    "approval_mode": "never",
                    "result_delivery": "none",
                    "execution_target_mode": "manual",
                    "execution_targets": [
                        {
                            "target_type": "department_table",
                            "target_ref": target_ref,
                            "provider": "custom_table",
                            "operation": "upsert_row",
                            "dept_route_mode": "current_dept",
                            "row_mapping": row_mapping,
                            "default_values": default_values,
                            "record_key_template": str(spec["record_key_template"]),
                            "idempotency_key_template": f"{workflow_code}:${{execution_id}}:${{node_id}}",
                        }
                    ],
                },
            },
        ],
        "edges": [
            {
                "id": "edge_parts_demand_to_execution",
                "source": "sensor_parts_demand",
                "target": "execution_fanout",
            }
        ],
    }


def _build_dialog_order_ui_schema(spec: dict[str, object]) -> dict[str, object]:
    input_schema = json.loads(json.dumps(spec["input_schema"], ensure_ascii=False))
    return {
        "nodes": [
            {
                "id": "dialog_sales_order",
                "type": "dialog_agent",
                "label": "销售订单入口",
                "config": {
                    "triggerSummary": str(spec["summary"]),
                    "triggerSynonyms": cast(list[str], spec["synonyms"]),
                    "triggerExampleUtterances": cast(list[str], spec["example_utterances"]),
                    "triggerRequiredInputs": cast(list[str], spec["required_inputs"]),
                    "triggerInputSchema": input_schema,
                },
            },
            {
                "id": "execution_customer_order",
                "type": "execution_agent",
                "label": "写入客户订单",
                "config": {
                    "approval_required": False,
                    "approval_mode": "never",
                    "result_delivery": "chat",
                    "execution_target_mode": "manual",
                    "execution_targets": [
                        {
                            "target_type": "department_table",
                            "target_ref": "customer_order",
                            "provider": "custom_table",
                            "operation": "upsert_row",
                            "dept_route_mode": "current_dept",
                            "row_mapping": {
                                "order_no": "decision_payload.order_no",
                                "customer_name": "decision_payload.customer_name",
                                "product_code": "decision_payload.product_code",
                                "product_name": "decision_payload.product_name",
                                "ordered_qty": "decision_payload.ordered_qty",
                                "unit_price": "decision_payload.unit_price",
                                "order_status": "decision_payload.order_status",
                            },
                            "default_values": {
                                "order_status": "draft",
                            },
                            "record_key_template": "{{decision_payload.order_no}}",
                            "idempotency_key_template": "dialog-sales-order-intake:${execution_id}:${node_id}",
                        }
                    ],
                },
            },
        ],
        "edges": [
            {
                "id": "edge_dialog_to_customer_order",
                "source": "dialog_sales_order",
                "target": "execution_customer_order",
            }
        ],
    }


def _build_order_projection_ui_schema(spec: dict[str, object]) -> dict[str, object]:
    return {
        "nodes": [
            {
                "id": "sensor_customer_order",
                "type": "sensor_agent",
                "label": "客户订单感知",
                "config": {
                    "source_type": "form_change",
                    "source_system": "erp_prod",
                    "source_table": "customer_order",
                    "source_event_key": "",
                },
            },
            {
                "id": "decision_parts_projection",
                "type": "decision_agent",
                "label": "订单拆解决策",
                "config": {
                    "decision_mode": "rule",
                    "rule_set_ref": "parts_demand_projection",
                    "rule_config": {
                        "action_type": "replace_department_table_rows",
                    },
                },
            },
            {
                "id": "execution_parts_demand",
                "type": "execution_agent",
                "label": "重建零件需求表",
                "config": {
                    "approval_required": False,
                    "approval_mode": "never",
                    "result_delivery": "none",
                    "execution_target_mode": "manual",
                    "execution_targets": [
                        {
                            "target_type": "department_table",
                            "target_ref": "parts_demand",
                            "provider": "custom_table",
                            "operation": "replace_rows",
                            "dept_route_mode": "current_dept",
                            "replace_by_field": "order_no",
                            "replace_by_value": "decision_payload.replace_by.value",
                            "record_key_template": "{{payload.order_no}}:{{payload.part_code}}:{{payload.source_type}}",
                            "idempotency_key_template": "customer-order-parts-demand-projection:${execution_id}:${node_id}",
                        }
                    ],
                },
            },
        ],
        "edges": [
            {
                "id": "edge_customer_order_to_decision",
                "source": "sensor_customer_order",
                "target": "decision_parts_projection",
            },
            {
                "id": "edge_decision_to_parts_demand",
                "source": "decision_parts_projection",
                "target": "execution_parts_demand",
            },
        ],
    }
