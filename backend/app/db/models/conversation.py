"""
Conversation model for storing chat conversations
"""
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.message import Message


class Conversation(Base, TimestampMixin):
    """
    Conversation model for storing chat conversations between user and AI.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of user who owns this conversation",
    )
    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Conversation title",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether conversation is active",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
        doc="User who owns this conversation",
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        doc="Messages in this conversation",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
