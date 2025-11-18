"""
SQLAlchemy declarative base and base model
"""
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all database models.
    Provides common functionality and type annotations.
    """

    # This will be overridden in child classes
    __abstract__ = True

    def dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated",
    )


# Import all models here for Alembic to detect them
from app.db.models.user import User  # noqa: F401
from app.db.models.conversation import Conversation  # noqa: F401
from app.db.models.message import Message  # noqa: F401

__all__ = ["Base", "TimestampMixin", "User", "Conversation", "Message"]
