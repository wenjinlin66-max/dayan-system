from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApprovalTask(Base):
    __tablename__: str = "approval_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    go_approval_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    execution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
