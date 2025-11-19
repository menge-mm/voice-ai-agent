"""
Seed default user for testing
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import async_session
from app.db.base import Base
from app.db.models import User


async def create_default_user():
    """Create default user if it doesn't exist"""
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=1,
                email='default@example.com',
                hashed_password='not-used',
                full_name='Default User',
                is_active=True,
                is_superuser=False
            )
            session.add(user)
            await session.commit()
            print('✓ Created default user (id=1, email=default@example.com)')
        else:
            print(f'✓ Default user already exists (id={user.id}, email={user.email})')


if __name__ == '__main__':
    asyncio.run(create_default_user())
