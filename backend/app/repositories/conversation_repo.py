"""
Conversation repository for conversation-specific database operations.

This extends the base repository with conversation-specific methods
like message management and user conversation retrieval.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.db.models.conversation import Conversation
from app.db.models.message import Message


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation entity with specialized operations.

    This repository provides conversation-specific methods beyond basic CRUD:
    - Get or create conversations
    - Message management
    - User conversation retrieval
    - Conversation history loading

    Example:
        ```python
        from app.db.session import get_db

        async with get_db() as session:
            repo = ConversationRepository(session)
            conversation = await repo.get_or_create("conv-123", user_id=1)
            await repo.add_messages(conversation.id, [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ])
        ```
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the conversation repository.

        Args:
            db: Async database session
        """
        super().__init__(Conversation, db)

    async def get_or_create(
        self,
        conversation_id: str,
        user_id: int,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Get an existing conversation or create a new one.

        This is useful for ensuring a conversation exists before adding messages.
        If the conversation already exists, it returns the existing one.

        Args:
            conversation_id: Unique identifier for the conversation
            user_id: ID of the user who owns the conversation
            title: Optional title for the conversation

        Returns:
            The existing or newly created conversation

        Example:
            ```python
            conv = await repo.get_or_create("conv-abc123", user_id=1)
            ```
        """
        # Try to find existing conversation by the string ID
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new conversation with the provided string ID
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title=title,
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def add_messages(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]]
    ) -> List[Message]:
        """
        Add multiple messages to a conversation.

        Each message should have at minimum 'role' and 'content' fields.
        Optional fields: audio_url, tokens_used

        Args:
            conversation_id: ID of the conversation
            messages: List of message dictionaries

        Returns:
            List of created Message objects

        Example:
            ```python
            messages = await repo.add_messages("conv-123", [
                {"role": "user", "content": "What is AI?"},
                {"role": "assistant", "content": "AI is..."},
            ])
            ```
        """
        created_messages = []

        for msg_data in messages:
            message = Message(
                conversation_id=conversation_id,
                role=msg_data["role"],
                content=msg_data["content"],
                audio_url=msg_data.get("audio_url"),
                tokens_used=msg_data.get("tokens_used"),
            )
            self.db.add(message)
            created_messages.append(message)

        await self.db.commit()

        # Refresh all messages to get generated IDs and timestamps
        for message in created_messages:
            await self.db.refresh(message)

        return created_messages

    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Message]:
        """
        Get all messages for a conversation in chronological order.

        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of messages ordered by creation time

        Example:
            ```python
            # Get all messages
            messages = await repo.get_messages("conv-123")

            # Get last 10 messages
            recent = await repo.get_messages("conv-123", limit=10)
            ```
        """
        stmt = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())

        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_with_messages(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """
        Get a conversation with all its messages eagerly loaded.

        This uses SQLAlchemy's selectinload to avoid N+1 queries.
        All messages are loaded in a single additional query.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation with messages loaded, or None if not found

        Example:
            ```python
            conv = await repo.get_with_messages("conv-123")
            if conv:
                for msg in conv.messages:
                    print(f"{msg.role}: {msg.content}")
            ```
        """
        stmt = select(Conversation).where(
            Conversation.id == conversation_id
        ).options(
            selectinload(Conversation.messages)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self,
        user_id: int,
        active_only: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Conversation]:
        """
        Get all conversations for a specific user.

        Args:
            user_id: ID of the user
            active_only: If True, only return active conversations
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of conversations ordered by most recent first

        Example:
            ```python
            # Get all user conversations
            all_convs = await repo.get_user_conversations(user_id=1)

            # Get only active conversations
            active = await repo.get_user_conversations(user_id=1, active_only=True)

            # Pagination
            page1 = await repo.get_user_conversations(user_id=1, limit=10)
            page2 = await repo.get_user_conversations(user_id=1, limit=10, offset=10)
            ```
        """
        stmt = select(Conversation).where(
            Conversation.user_id == user_id
        )

        if active_only:
            stmt = stmt.where(Conversation.is_active == True)

        # Order by most recent first
        stmt = stmt.order_by(Conversation.updated_at.desc())

        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Due to CASCADE delete in the database schema, all associated
        messages will also be deleted automatically.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if deleted, False if not found

        Example:
            ```python
            success = await repo.delete("conv-123")
            # All messages in this conversation are also deleted
            ```
        """
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            return False

        await self.db.delete(conversation)
        await self.db.commit()
        return True

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by its string ID.

        Overrides base repository method to handle string IDs.

        Args:
            conversation_id: The conversation ID (string)

        Returns:
            The conversation if found, None otherwise
        """
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        conversation_id: str,
        data: Dict[str, Any]
    ) -> Optional[Conversation]:
        """
        Update a conversation.

        Args:
            conversation_id: ID of the conversation to update
            data: Dictionary of fields to update

        Returns:
            The updated conversation if found, None otherwise

        Example:
            ```python
            conv = await repo.update("conv-123", {
                "title": "My AI Chat",
                "is_active": False
            })
            ```
        """
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            return None

        for key, value in data.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)

        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
