from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class AntiFloodMiddleware(BaseMiddleware):
    """
    防刷中间件：限制同一会话在短时间内的重复触发。

    参数：
        time_limit: 同一会话的最小触发间隔（秒）。默认 1 秒。
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
