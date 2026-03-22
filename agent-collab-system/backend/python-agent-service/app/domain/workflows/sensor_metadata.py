from __future__ import annotations

from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sensor_metadata import (
    SensorEventKeyOption,
    SensorFieldOption,
    SensorMetadataResponse,
    SensorOperatorOption,
    SensorSourceOption,
    SensorSourceTypeOption,
    SensorTableOption,
)


class SensorMetadataService:
    def build_default_metadata(self) -> SensorMetadataResponse:
        return SensorMetadataResponse(
            source_types=[
                SensorSourceTypeOption(value="form_change", label="数据库记录变更"),
                SensorSourceTypeOption(value="iot", label="IoT 状态上报"),
                SensorSourceTypeOption(value="supply_chain_event", label="供应链事件"),
                SensorSourceTypeOption(value="third_party_notice", label="第三方通知"),
                SensorSourceTypeOption(value="schedule", label="定时巡检"),
                SensorSourceTypeOption(value="manual", label="手动 / Mock"),
            ],
            operators=[
                SensorOperatorOption(value="eq", label="等于", supported_field_types=["string", "number", "boolean"]),
                SensorOperatorOption(value="ne", label="不等于", supported_field_types=["string", "number", "boolean"]),
                SensorOperatorOption(value=">", label="大于", supported_field_types=["number"]),
                SensorOperatorOption(value=">=", label="大于等于", supported_field_types=["number"]),
                SensorOperatorOption(value="<", label="小于", supported_field_types=["number"]),
                SensorOperatorOption(value="<=", label="小于等于", supported_field_types=["number"]),
            ],
            sources=[
                SensorSourceOption(
                    value="erp_prod",
                    label="ERP 生产库",
                    source_type="form_change",
                    tables=[
                        SensorTableOption(
                            value="parts_demand",
                            label="零件需求表 parts_demand",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                                SensorEventKeyOption(value="record.deleted", label="记录删除"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_no", label="订单编号", field_type="string"),
                                SensorFieldOption(value="product_code", label="产品编码", field_type="string"),
                                SensorFieldOption(value="part_code", label="零件编码", field_type="string"),
                                SensorFieldOption(value="source_type", label="来源类型", field_type="string", suggested_values=["purchase", "manufacture", "customer"]),
                                SensorFieldOption(value="required_qty", label="总需求数", field_type="number"),
                                SensorFieldOption(value="purchase_qty", label="采购需求数", field_type="number"),
                                SensorFieldOption(value="manufacture_qty", label="生产需求数", field_type="number"),
                                SensorFieldOption(value="customer_qty", label="客户提供数", field_type="number"),
                            ],
                        ),
                        SensorTableOption(
                            value="purchase_request",
                            label="销售/采购部表单 purchase_request",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_no", label="订单编号", field_type="string"),
                                SensorFieldOption(value="part_code", label="零件编码", field_type="string"),
                                SensorFieldOption(value="request_qty", label="申请数量", field_type="number"),
                                SensorFieldOption(value="request_status", label="表单状态", field_type="string"),
                            ],
                        ),
                        SensorTableOption(
                            value="manufacturing_request",
                            label="生产部表单 manufacturing_request",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_no", label="订单编号", field_type="string"),
                                SensorFieldOption(value="part_code", label="零件编码", field_type="string"),
                                SensorFieldOption(value="request_qty", label="生产数量", field_type="number"),
                                SensorFieldOption(value="request_status", label="表单状态", field_type="string"),
                            ],
                        ),
                        SensorTableOption(
                            value="customer_supply_request",
                            label="客户配合表单 customer_supply_request",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_no", label="订单编号", field_type="string"),
                                SensorFieldOption(value="part_code", label="零件编码", field_type="string"),
                                SensorFieldOption(value="request_qty", label="客户提供数", field_type="number"),
                                SensorFieldOption(value="request_status", label="表单状态", field_type="string"),
                            ],
                        ),
                        SensorTableOption(
                            value="product_master",
                            label="产品主表 product_master",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="product_code", label="产品编码", field_type="string"),
                                SensorFieldOption(value="product_name", label="产品名称", field_type="string"),
                                SensorFieldOption(value="unit_price", label="标准售价", field_type="number"),
                            ],
                        ),
                        SensorTableOption(
                            value="product_bom",
                            label="产品 BOM product_bom",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="product_code", label="产品编码", field_type="string"),
                                SensorFieldOption(value="part_code", label="零件编码", field_type="string"),
                                SensorFieldOption(value="qty_per_unit", label="单件用量", field_type="number"),
                                SensorFieldOption(value="source_type", label="来源类型", field_type="string", suggested_values=["purchase", "manufacture", "customer"]),
                            ],
                        ),
                        SensorTableOption(
                            value="customer_order",
                            label="客户订单 customer_order",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_no", label="订单编号", field_type="string"),
                                SensorFieldOption(value="product_code", label="产品编码", field_type="string"),
                                SensorFieldOption(value="ordered_qty", label="订单数量", field_type="number"),
                                SensorFieldOption(value="order_status", label="订单状态", field_type="string"),
                            ],
                        ),
                    ],
                ),
            ],
        )

    async def get_metadata(self, session: AsyncSession) -> SensorMetadataResponse:
        metadata = self.build_default_metadata()
        live_source = await self._build_live_database_source(session)
        if live_source is not None:
            metadata.sources.insert(0, live_source)
        return metadata

    async def _build_live_database_source(self, session: AsyncSession) -> SensorSourceOption | None:
        result = await session.execute(
            text(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            )
        )
        rows = result.mappings().all()
        if not rows:
            return None

        tables: dict[str, list[SensorFieldOption]] = defaultdict(list)
        for row in rows:
            table_name = str(row.get("table_name") or "")
            column_name = str(row.get("column_name") or "")
            data_type = str(row.get("data_type") or "")
            if not table_name or not column_name:
                continue
            tables[table_name].append(
                SensorFieldOption(
                    value=column_name,
                    label=column_name,
                    field_type=self._map_field_type(data_type),
                )
            )

        table_options = [
            SensorTableOption(
                value=table_name,
                label=f"实时数据库表 {table_name}",
                event_keys=[
                    SensorEventKeyOption(value="record.updated", label="记录更新"),
                    SensorEventKeyOption(value="record.created", label="记录新增"),
                    SensorEventKeyOption(value="record.deleted", label="记录删除"),
                ],
                fields=fields,
            )
            for table_name, fields in tables.items()
        ]

        return SensorSourceOption(
            value="postgres_live",
            label="当前后端数据库（实时表结构）",
            source_type="form_change",
            tables=table_options,
        )

    @staticmethod
    def _map_field_type(data_type: str) -> str:
        normalized = data_type.lower()
        if any(keyword in normalized for keyword in ["int", "numeric", "double", "real", "decimal"]):
            return "number"
        if normalized in {"boolean", "bool"}:
            return "boolean"
        return "string"
