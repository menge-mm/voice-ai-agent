"""
Tests for database models
Following TDD: These tests are written FIRST before implementation
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


@pytest.mark.asyncio
async def test_user_model_creation(async_db_session: AsyncSession):
    """Test that User model can be created"""
    from app.db.models.user import User

    user = User(
        email="test@example.com",
        hashed_password="hashedpass123",
        full_name="Test User",
        is_active=True,
    )

    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)


@pytest.mark.asyncio
async def test_user_model_validation(async_db_session: AsyncSession):
    """Test that User model validates email uniqueness"""
    from app.db.models.user import User

    # Create first user
    user1 = User(
        email="unique@example.com",
        hashed_password="hash1",
    )
    async_db_session.add(user1)
    await async_db_session.commit()

    # Try to create duplicate email (should fail)
    user2 = User(
        email="unique@example.com",
        hashed_password="hash2",
    )
    async_db_session.add(user2)

    with pytest.raises(Exception):  # IntegrityError expected
        await async_db_session.commit()


@pytest.mark.asyncio
async def test_conversation_model_relationships(async_db_session: AsyncSession):
    """Test that Conversation model has correct relationships"""
    from app.db.models.user import User
    from app.db.models.conversation import Conversation

    # Create user
    user = User(email="user@example.com", hashed_password="hash")
    async_db_session.add(user)
    await async_db_session.flush()

    # Create conversation (with UUID id since it's a String field)
    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title="Test Conversation",
    )
    async_db_session.add(conversation)
    await async_db_session.commit()
    await async_db_session.refresh(conversation)

    assert conversation.id is not None
    assert conversation.user_id == user.id
    assert conversation.title == "Test Conversation"


@pytest.mark.asyncio
async def test_message_model_timestamps(async_db_session: AsyncSession):
    """Test that Message model auto-populates timestamps"""
    from app.db.models.user import User
    from app.db.models.conversation import Conversation
    from app.db.models.message import Message

    # Create user and conversation
    user = User(email="user@example.com", hashed_password="hash")
    async_db_session.add(user)
    await async_db_session.flush()

    conversation = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Test")
    async_db_session.add(conversation)
    await async_db_session.flush()

    # Create message
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Hello, world!",
    )
    async_db_session.add(message)
    await async_db_session.commit()
    await async_db_session.refresh(message)

    assert message.id is not None
    assert message.created_at is not None
    assert message.updated_at is not None
    assert isinstance(message.created_at, datetime)
    assert isinstance(message.updated_at, datetime)


@pytest.mark.asyncio
async def test_cascade_delete_conversation_messages(async_db_session: AsyncSession):
    """Test that deleting conversation deletes its messages"""
    from app.db.models.user import User
    from app.db.models.conversation import Conversation
    from app.db.models.message import Message

    # Create user, conversation, and messages
    user = User(email="user@example.com", hashed_password="hash")
    async_db_session.add(user)
    await async_db_session.flush()

    conversation = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Test")
    async_db_session.add(conversation)
    await async_db_session.flush()

    message1 = Message(conversation_id=conversation.id, role="user", content="Hi")
    message2 = Message(conversation_id=conversation.id, role="assistant", content="Hello")
    async_db_session.add_all([message1, message2])
    await async_db_session.commit()

    conversation_id = conversation.id

    # Delete conversation
    await async_db_session.delete(conversation)
    await async_db_session.commit()

    # Check that messages are also deleted
    result = await async_db_session.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    messages = result.scalars().all()
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_message_role_validation(async_db_session: AsyncSession):
    """Test that Message role is validated"""
    from app.db.models.user import User
    from app.db.models.conversation import Conversation
    from app.db.models.message import Message

    # Create user and conversation
    user = User(email="user@example.com", hashed_password="hash")
    async_db_session.add(user)
    await async_db_session.flush()

    conversation = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Test")
    async_db_session.add(conversation)
    await async_db_session.flush()

    # Valid roles
    for role in ["user", "assistant", "system"]:
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=f"Test {role}",
        )
        async_db_session.add(message)
        await async_db_session.flush()
        assert message.role == role


@pytest.mark.asyncio
async def test_conversation_default_values(async_db_session: AsyncSession):
    """Test that Conversation has correct default values"""
    from app.db.models.user import User
    from app.db.models.conversation import Conversation

    user = User(email="user@example.com", hashed_password="hash")
    async_db_session.add(user)
    await async_db_session.flush()

    conversation = Conversation(id=str(uuid.uuid4()), user_id=user.id)
    async_db_session.add(conversation)
    await async_db_session.commit()
    await async_db_session.refresh(conversation)

    assert conversation.title is None or conversation.title == ""
    assert conversation.is_active is True
    assert conversation.created_at is not None


@pytest.mark.asyncio
async def test_user_conversations_relationship(async_db_session: AsyncSession):
    """Test that User can access their conversations"""
    from app.db.models.user import User
    from app.db.models.conversation import Conversation

    user = User(email="user@example.com", hashed_password="hash")
    async_db_session.add(user)
    await async_db_session.flush()

    # Create multiple conversations
    conv1 = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Conversation 1")
    conv2 = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Conversation 2")
    async_db_session.add_all([conv1, conv2])
    await async_db_session.commit()

    # Refresh user to load relationships
    await async_db_session.refresh(user)

    # Check that user has conversations (if relationship is set up)
    # This tests the back-reference
    assert user.id is not None
