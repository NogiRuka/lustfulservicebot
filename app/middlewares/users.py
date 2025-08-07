from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from app.database.users import add_user, update_last_acitivity


class AddUser(BaseMiddleware):
    """
    Initialize the middleware with a time limit.

    Args:
        time_limit: The time limit in seconds for the same message
            to be sent to the same chat. Defaults to 1 second.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        await add_user(event.chat.id, event.chat.full_name, event.chat.username)

        return await handler(event, data)


class UpdateLastAcivity(BaseMiddleware):
    """
    Initialize the middleware with a time limit.

    Args:
        time_limit: The time limit in seconds for the same message
            to be sent to the same chat. Defaults to 1 second.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:

        await update_last_acitivity(event.chat.id)

        return await handler(event, data)
