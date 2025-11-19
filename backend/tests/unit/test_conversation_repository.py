"""
Unit tests for conversation repository.

Following TDD - these tests define the behavior of conversation-specific
operations beyond basic CRUD.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.base import BaseRepository
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.message import Message


class TestConversationRepository:
    """Test suite for ConversationRepository."""

    @pytest.mark.asyncio
    async def test_get_or_create_new_conversation(self, async_db_session: AsyncSession):
        """Test creating a new conversation when it doesn't exist."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation_id = "conv-12345"

        # Act
        conversation = await conv_repo.get_or_create(
            conversation_id=conversation_id,
            user_id=user.id
        )

        # Assert
        assert conversation is not None
        assert conversation.id == conversation_id
        assert conversation.user_id == user.id
        assert conversation.is_active is True
        assert conversation.created_at is not None

    @pytest.mark.asyncio
    async def test_get_or_create_existing_conversation(self, async_db_session: AsyncSession):
        """Test retrieving an existing conversation."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation_id = "conv-existing"

        # Create conversation first
        first_conv = await conv_repo.get_or_create(
            conversation_id=conversation_id,
            user_id=user.id
        )

        # Act - Get the same conversation
        second_conv = await conv_repo.get_or_create(
            conversation_id=conversation_id,
            user_id=user.id
        )

        # Assert - Should be the same conversation
        assert second_conv.id == first_conv.id
        assert second_conv.user_id == first_conv.user_id
        assert second_conv.created_at == first_conv.created_at

    @pytest.mark.asyncio
    async def test_add_messages_to_conversation(self, async_db_session: AsyncSession):
        """Test adding messages to a conversation."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation = await conv_repo.get_or_create(
            conversation_id="conv-messages",
            user_id=user.id
        )

        messages_data = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Act
        messages = await conv_repo.add_messages(
            conversation_id=conversation.id,
            messages=messages_data
        )

        # Assert
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[0].conversation_id == conversation.id
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi there!"
        assert messages[1].conversation_id == conversation.id

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, async_db_session: AsyncSession):
        """Test retrieving messages from a conversation."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation = await conv_repo.get_or_create(
            conversation_id="conv-get-messages",
            user_id=user.id
        )

        # Add some messages
        await conv_repo.add_messages(
            conversation_id=conversation.id,
            messages=[
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Second message"},
                {"role": "user", "content": "Third message"},
            ]
        )

        # Act
        messages = await conv_repo.get_messages(conversation.id)

        # Assert
        assert len(messages) == 3
        assert messages[0].content == "First message"
        assert messages[1].content == "Second message"
        assert messages[2].content == "Third message"
        # Should be in chronological order
        assert messages[0].created_at <= messages[1].created_at
        assert messages[1].created_at <= messages[2].created_at

    @pytest.mark.asyncio
    async def test_get_conversation_messages_with_limit(self, async_db_session: AsyncSession):
        """Test retrieving limited number of messages."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation = await conv_repo.get_or_create(
            conversation_id="conv-limit",
            user_id=user.id
        )

        # Add 5 messages
        await conv_repo.add_messages(
            conversation_id=conversation.id,
            messages=[
                {"role": "user", "content": f"Message {i}"}
                for i in range(5)
            ]
        )

        # Act - Get last 3 messages
        messages = await conv_repo.get_messages(conversation.id, limit=3)

        # Assert
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_get_conversation_with_messages(self, async_db_session: AsyncSession):
        """Test retrieving a conversation with all its messages loaded."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation = await conv_repo.get_or_create(
            conversation_id="conv-with-messages",
            user_id=user.id
        )

        await conv_repo.add_messages(
            conversation_id=conversation.id,
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
            ]
        )

        # Act
        conv_with_messages = await conv_repo.get_with_messages(conversation.id)

        # Assert
        assert conv_with_messages is not None
        assert conv_with_messages.id == conversation.id
        assert len(conv_with_messages.messages) == 2
        assert conv_with_messages.messages[0].content == "Hello"
        assert conv_with_messages.messages[1].content == "Hi!"

    @pytest.mark.asyncio
    async def test_delete_conversation_cascade(self, async_db_session: AsyncSession):
        """Test that deleting a conversation also deletes its messages (CASCADE)."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation = await conv_repo.get_or_create(
            conversation_id="conv-cascade",
            user_id=user.id
        )

        # Add messages
        added_messages = await conv_repo.add_messages(
            conversation_id=conversation.id,
            messages=[
                {"role": "user", "content": "Message 1"},
                {"role": "assistant", "content": "Message 2"},
            ]
        )
        message_ids = [msg.id for msg in added_messages]

        # Act - Delete conversation
        result = await conv_repo.delete(conversation.id)

        # Assert - Conversation deleted
        assert result is True
        deleted_conv = await conv_repo.get_by_id(conversation.id)
        assert deleted_conv is None

        # Assert - Messages also deleted (CASCADE)
        message_repo = BaseRepository(Message, async_db_session)
        for msg_id in message_ids:
            msg = await message_repo.get_by_id(msg_id)
            assert msg is None, "Messages should be deleted with conversation (CASCADE)"

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, async_db_session: AsyncSession):
        """Test retrieving all conversations for a specific user."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)

        # Create multiple conversations for the user
        await conv_repo.get_or_create("conv-1", user.id)
        await conv_repo.get_or_create("conv-2", user.id)
        await conv_repo.get_or_create("conv-3", user.id)

        # Act
        conversations = await conv_repo.get_user_conversations(user.id)

        # Assert
        assert len(conversations) == 3
        for conv in conversations:
            assert conv.user_id == user.id

    @pytest.mark.asyncio
    async def test_get_user_active_conversations(self, async_db_session: AsyncSession):
        """Test retrieving only active conversations for a user."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)

        # Create active and inactive conversations
        active_conv = await conv_repo.get_or_create("conv-active", user.id)
        inactive_conv = await conv_repo.get_or_create("conv-inactive", user.id)

        # Mark one as inactive
        await conv_repo.update(inactive_conv.id, {"is_active": False})

        # Act
        active_conversations = await conv_repo.get_user_conversations(
            user.id,
            active_only=True
        )

        # Assert
        assert len(active_conversations) == 1
        assert active_conversations[0].id == active_conv.id
        assert active_conversations[0].is_active is True

    @pytest.mark.asyncio
    async def test_update_conversation_title(self, async_db_session: AsyncSession):
        """Test updating a conversation's title."""
        # Arrange
        user_repo = BaseRepository(User, async_db_session)
        user = await user_repo.create({
            "email": "test@example.com",
            "hashed_password": "hashed",
        })

        conv_repo = ConversationRepository(async_db_session)
        conversation = await conv_repo.get_or_create("conv-title", user.id)

        # Act
        updated_conv = await conv_repo.update(
            conversation.id,
            {"title": "My Chat About AI"}
        )

        # Assert
        assert updated_conv is not None
        assert updated_conv.title == "My Chat About AI"
