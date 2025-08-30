from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache
from app.config.config import GROUP
from app.utils.group_utils import user_in_group_filter
from loguru import logger


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


class GroupVerificationMiddleware(BaseMiddleware):
    """
    群组验证中间件：确保用户仍在指定群组中才能使用机器人功能。
    适用于回调查询（按钮点击）的验证。
    """

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # 如果没有设置群组，则跳过验证
        if not GROUP:
            return await handler(event, data)
        
        try:
            # 检查用户是否仍在群组中
            is_in_group = await user_in_group_filter(event.bot, event.from_user.id)
            
            if not is_in_group:
                # 用户已退出群组，显示提示信息
                await event.answer(
                    f"❌ 您已退出群组 @{GROUP}，无法继续使用机器人功能。\n\n"
                    "请重新加入群组后再试。",
                    show_alert=True
                )
                return
            
            # 用户仍在群组中，继续处理
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"群组验证中间件错误: {e}")
            # 发生错误时，为了安全起见，拒绝访问
            await event.answer(
                "❌ 验证失败，请稍后重试。",
                show_alert=True
            )
            return
