from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_dept_id: Mapped[str] = mapped_column(String(64), nullable=False)
    current_release_version: Mapped[int | None] = mapped_column(Integer, nullable=True)


class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    release_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
