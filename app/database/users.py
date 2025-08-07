from sqlalchemy import select, update
from datetime import datetime
from loguru import logger

from app.database.db import get_db
from app.database.schema import User


async def add_user(chat_id: int, full_name: str, username: str) -> bool:
    """
    Adding user to the database
    """
    async for session in get_db():
        try:
            # Check if the user already exists
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            is_exists = result.scalars().first()

            if not is_exists:
                created_at = datetime.now()
                new_user = User(
                    chat_id=chat_id,
                    full_name=full_name,
                    username=username,
                    created_at=created_at,
                )
                session.add(new_user)
                await session.commit()  # Commit the transaction
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            await session.rollback()  # Rollback in case of error
            return False


async def get_user(chat_id: int) -> User | None:
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            await session.rollback()
            return None


async def set_busy(chat_id: int, is_busy: bool) -> None:
    async for session in get_db():
        try:
            await session.execute(
                update(User).filter_by(chat_id=chat_id).values(is_busy=is_busy)
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error setting busy status: {e}")
            await session.rollback()


async def get_busy(chat_id: int) -> bool:
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user.is_busy
        except Exception as e:
            logger.error(f"Error getting busy status: {e}")
            await session.rollback()
            return False


async def update_last_acitivity(chat_id: int) -> None:
    async for session in get_db():
        try:
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values(last_activity_at=datetime.now())
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error updating last activity: {e}")
            await session.rollback()
