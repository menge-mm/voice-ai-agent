"""
User model for authentication and user management
"""
from typing import List
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for storing user information and authentication.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User email address (unique)",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Hashed password",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User's full name",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether user account is active",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether user has superuser privileges",
    )

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's conversations",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
