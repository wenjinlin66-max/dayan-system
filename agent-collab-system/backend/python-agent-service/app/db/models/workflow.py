from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_dept_id: Mapped[str] = mapped_column(String(64), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), default="private", nullable=False)
    latest_draft_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_release_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    ui_schema: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    execution_dag: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    compile_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    compile_errors: Mapped[list[object] | None] = mapped_column(JSON, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="2026-03")
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    release_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_current_release: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowRegistry(Base):
    __tablename__ = "workflow_registry"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    workflow_version: Mapped[int] = mapped_column(Integer, nullable=False)
    dept_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    synonyms: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    example_utterances: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    allowed_roles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    required_inputs: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    input_schema: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    approval_policy: Mapped[str] = mapped_column(String(64), default="risk_based", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    output_contract: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
