from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from app.database.users import add_user, update_last_acitivity


class AddUser(BaseMiddleware):
    """
    用户入库中间件：
    - 首次交互时将用户信息写入数据库（幂等）。
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
    活跃时间更新中间件：
    - 每次消息到达时更新用户的最近活跃时间。
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:

        await update_last_acitivity(event.chat.id)

        return await handler(event, data)
