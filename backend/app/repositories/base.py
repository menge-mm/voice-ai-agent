"""
Base repository pattern for generic CRUD operations.

This implements the repository pattern to abstract database operations
and provide a clean interface for data access.
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy import select, func, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

# Generic type for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with generic CRUD operations.

    This class provides common database operations for any SQLAlchemy model.
    It uses async/await pattern for non-blocking database access.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages

    Example:
        ```python
        from app.db.models.user import User
        from app.db.session import get_db

        async with get_db() as session:
            user_repo = BaseRepository(User, session)
            user = await user_repo.create({"email": "test@example.com"})
        ```
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize the repository.

        Args:
            model: The SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new entity.

        Args:
            data: Dictionary of field values

        Returns:
            The created entity

        Example:
            ```python
            user = await repo.create({"email": "test@example.com", "name": "Test"})
            ```
        """
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, entity_id: int) -> Optional[ModelType]:
        """
        Retrieve an entity by its primary key ID.

        Args:
            entity_id: The primary key ID

        Returns:
            The entity if found, None otherwise

        Example:
            ```python
            user = await repo.get_by_id(123)
            if user:
                print(user.email)
            ```
        """
        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """
        Retrieve all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities

        Example:
            ```python
            # Get first 10 users
            users = await repo.get_all(limit=10)

            # Get next 10 users (pagination)
            users = await repo.get_all(limit=10, offset=10)
            ```
        """
        stmt = select(self.model)

        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        entity_id: int,
        data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update an existing entity.

        Args:
            entity_id: The ID of the entity to update
            data: Dictionary of fields to update

        Returns:
            The updated entity if found, None otherwise

        Example:
            ```python
            updated_user = await repo.update(123, {"name": "New Name"})
            ```
        """
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return None

        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: The ID of the entity to delete

        Returns:
            True if deleted, False if not found

        Example:
            ```python
            success = await repo.delete(123)
            if success:
                print("User deleted")
            ```
        """
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return False

        await self.db.delete(entity)
        await self.db.commit()
        return True

    async def get_by_field(
        self,
        field_name: str,
        value: Any
    ) -> Optional[ModelType]:
        """
        Retrieve an entity by a specific field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match

        Returns:
            The first matching entity, or None

        Example:
            ```python
            user = await repo.get_by_field("email", "test@example.com")
            ```
        """
        if not hasattr(self.model, field_name):
            return None

        field = getattr(self.model, field_name)
        stmt = select(self.model).where(field == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def filter_by(self, **kwargs) -> List[ModelType]:
        """
        Filter entities by multiple field values.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            List of matching entities

        Example:
            ```python
            # Find all active users
            active_users = await repo.filter_by(is_active=True)

            # Find users by multiple criteria
            users = await repo.filter_by(is_active=True, role="admin")
            ```
        """
        stmt = select(self.model)

        for field_name, value in kwargs.items():
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                stmt = stmt.where(field == value)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count

        Example:
            ```python
            total_users = await repo.count()
            print(f"Total users: {total_users}")
            ```
        """
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists by ID.

        Args:
            entity_id: The ID to check

        Returns:
            True if exists, False otherwise

        Example:
            ```python
            if await repo.exists(123):
                print("User exists")
            ```
        """
        entity = await self.get_by_id(entity_id)
        return entity is not None
