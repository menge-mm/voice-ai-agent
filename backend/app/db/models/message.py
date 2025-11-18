"""
Message model for storing chat messages
"""
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation


class Message(Base, TimestampMixin):
    """
    Message model for storing individual chat messages in a conversation.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of conversation this message belongs to",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Message role: 'user', 'assistant', or 'system'",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Message content/text",
    )
    audio_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="URL to audio file if TTS was generated",
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of tokens used for this message (if applicable)",
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
        doc="Conversation this message belongs to",
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role='{self.role}', content='{content_preview}')>"
