from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class AntiFloodMiddleware(BaseMiddleware):
    """
    Initialize the middleware with a time limit.

    Args:
        time_limit: The time limit in seconds for the same message
            to be sent to the same chat. Defaults to 1 second.
    """

    def __init__(self, time_limit: int = 1):
        self.limit = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.chat.id in self.limit:
            return
        else:
            self.limit[event.chat.id] = None

        return await handler(event, data)
