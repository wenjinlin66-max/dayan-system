from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.mock_records.db.base import MockRecordsBase


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProductMasterRecord(MockRecordsBase):
    __tablename__: str = "product_master"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product_version: Mapped[str] = mapped_column(String(64), nullable=False, default="V1")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="成品")
    unit_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ProductBomRecord(MockRecordsBase):
    __tablename__: str = "product_bom"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False)
    qty_per_unit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="purchase")
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class CustomerOrderRecord(MockRecordsBase):
    __tablename__: str = "customer_order"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    ordered_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    order_status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PartsDemandRecord(MockRecordsBase):
    __tablename__: str = "parts_demand"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    part_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    required_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchase_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manufacture_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    customer_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PurchaseRequestRecord(MockRecordsBase):
    __tablename__: str = "purchase_request"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False)
    request_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    supplier_hint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    request_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ManufacturingRequestRecord(MockRecordsBase):
    __tablename__: str = "manufacturing_request"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False)
    request_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workshop_id: Mapped[str] = mapped_column(String(64), nullable=False, default="WS-ASM")
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    request_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class CustomerSupplyRequestRecord(MockRecordsBase):
    __tablename__: str = "customer_supply_request"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False)
    request_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    handoff_note: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class SensorChangeLogRecord(MockRecordsBase):
    __tablename__: str = "sensor_change_log"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False, default="dayan_mock_records")
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    before_data: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    after_data: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    triggered_execution_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
