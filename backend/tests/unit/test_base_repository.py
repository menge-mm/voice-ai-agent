"""
Unit tests for base repository pattern.

Following TDD approach - these tests are written FIRST to define
the expected behavior of the generic repository.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.db.models.user import User


class TestBaseRepository:
    """Test suite for BaseRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_repository_create(self, async_db_session: AsyncSession):
        """Test creating a new entity in the repository."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        user_data = {
            "email": "test@example.com",
            "hashed_password": "hashed_password_123",
            "full_name": "Test User",
        }

        # Act
        user = await repo.create(user_data)

        # Assert
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True  # Default value
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_repository_get_by_id(self, async_db_session: AsyncSession):
        """Test retrieving an entity by ID."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        user = await repo.create({
            "email": "get_test@example.com",
            "hashed_password": "hashed",
            "full_name": "Get Test",
        })

        # Act
        retrieved_user = await repo.get_by_id(user.id)

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == "get_test@example.com"

    @pytest.mark.asyncio
    async def test_repository_get_by_id_not_found(self, async_db_session: AsyncSession):
        """Test retrieving a non-existent entity returns None."""
        # Arrange
        repo = BaseRepository(User, async_db_session)

        # Act
        user = await repo.get_by_id(99999)

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_repository_get_all(self, async_db_session: AsyncSession):
        """Test retrieving all entities."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        await repo.create({
            "email": "user1@example.com",
            "hashed_password": "hashed",
        })
        await repo.create({
            "email": "user2@example.com",
            "hashed_password": "hashed",
        })
        await repo.create({
            "email": "user3@example.com",
            "hashed_password": "hashed",
        })

        # Act
        users = await repo.get_all()

        # Assert
        assert len(users) == 3
        emails = [u.email for u in users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails
        assert "user3@example.com" in emails

    @pytest.mark.asyncio
    async def test_repository_get_all_with_limit(self, async_db_session: AsyncSession):
        """Test retrieving entities with limit."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        for i in range(5):
            await repo.create({
                "email": f"user{i}@example.com",
                "hashed_password": "hashed",
            })

        # Act
        users = await repo.get_all(limit=3)

        # Assert
        assert len(users) == 3

    @pytest.mark.asyncio
    async def test_repository_get_all_with_offset(self, async_db_session: AsyncSession):
        """Test retrieving entities with offset."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        for i in range(5):
            await repo.create({
                "email": f"user{i}@example.com",
                "hashed_password": "hashed",
            })

        # Act
        users = await repo.get_all(offset=2)

        # Assert
        assert len(users) == 3  # 5 total - 2 offset

    @pytest.mark.asyncio
    async def test_repository_update(self, async_db_session: AsyncSession):
        """Test updating an existing entity."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        user = await repo.create({
            "email": "update@example.com",
            "hashed_password": "hashed",
            "full_name": "Original Name",
        })
        original_id = user.id

        # Act
        updated_user = await repo.update(user.id, {"full_name": "Updated Name"})

        # Assert
        assert updated_user is not None
        assert updated_user.id == original_id
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "update@example.com"  # Unchanged

    @pytest.mark.asyncio
    async def test_repository_update_not_found(self, async_db_session: AsyncSession):
        """Test updating a non-existent entity returns None."""
        # Arrange
        repo = BaseRepository(User, async_db_session)

        # Act
        updated_user = await repo.update(99999, {"full_name": "New Name"})

        # Assert
        assert updated_user is None

    @pytest.mark.asyncio
    async def test_repository_delete(self, async_db_session: AsyncSession):
        """Test deleting an entity."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        user = await repo.create({
            "email": "delete@example.com",
            "hashed_password": "hashed",
        })
        user_id = user.id

        # Act
        result = await repo.delete(user_id)

        # Assert
        assert result is True
        deleted_user = await repo.get_by_id(user_id)
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_repository_delete_not_found(self, async_db_session: AsyncSession):
        """Test deleting a non-existent entity returns False."""
        # Arrange
        repo = BaseRepository(User, async_db_session)

        # Act
        result = await repo.delete(99999)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_repository_get_by_field(self, async_db_session: AsyncSession):
        """Test retrieving entities by a specific field."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        await repo.create({
            "email": "field_test@example.com",
            "hashed_password": "hashed",
            "full_name": "Field Test User",
        })

        # Act
        user = await repo.get_by_field("email", "field_test@example.com")

        # Assert
        assert user is not None
        assert user.email == "field_test@example.com"
        assert user.full_name == "Field Test User"

    @pytest.mark.asyncio
    async def test_repository_get_by_field_not_found(self, async_db_session: AsyncSession):
        """Test retrieving by field that doesn't exist returns None."""
        # Arrange
        repo = BaseRepository(User, async_db_session)

        # Act
        user = await repo.get_by_field("email", "nonexistent@example.com")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_repository_filter_by(self, async_db_session: AsyncSession):
        """Test filtering entities by multiple criteria."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        await repo.create({
            "email": "active1@example.com",
            "hashed_password": "hashed",
            "is_active": True,
        })
        await repo.create({
            "email": "active2@example.com",
            "hashed_password": "hashed",
            "is_active": True,
        })
        await repo.create({
            "email": "inactive@example.com",
            "hashed_password": "hashed",
            "is_active": False,
        })

        # Act
        active_users = await repo.filter_by(is_active=True)

        # Assert
        assert len(active_users) == 2
        for user in active_users:
            assert user.is_active is True

    @pytest.mark.asyncio
    async def test_repository_count(self, async_db_session: AsyncSession):
        """Test counting entities in the repository."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        for i in range(7):
            await repo.create({
                "email": f"count{i}@example.com",
                "hashed_password": "hashed",
            })

        # Act
        count = await repo.count()

        # Assert
        assert count == 7

    @pytest.mark.asyncio
    async def test_repository_exists(self, async_db_session: AsyncSession):
        """Test checking if an entity exists."""
        # Arrange
        repo = BaseRepository(User, async_db_session)
        user = await repo.create({
            "email": "exists@example.com",
            "hashed_password": "hashed",
        })

        # Act
        exists = await repo.exists(user.id)
        not_exists = await repo.exists(99999)

        # Assert
        assert exists is True
        assert not_exists is False
