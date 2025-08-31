from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from cachetools import TTLCache
from app.config.config import GROUP
from app.utils.group_utils import user_in_group_filter
from app.database.business import is_feature_enabled
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


class BotStatusMiddleware(BaseMiddleware):
    """机器人状态检查中间件"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 检查机器人是否启用
        if not await is_feature_enabled("bot_enabled"):
            # 如果是消息事件，发送维护提示
            if hasattr(event, 'answer'):
                try:
                    await event.answer(
                        "🔧 机器人正在维护中，请稍后再试。\n\n"
                        "如有紧急问题，请联系管理员。",
                        show_alert=True
                    )
                except:
                    pass
            elif hasattr(event, 'reply'):
                try:
                    await event.reply(
                        "🔧 <b>机器人维护中</b>\n\n"
                        "系统正在进行维护升级，暂时无法提供服务。\n\n"
                        "📅 预计恢复时间：请关注公告\n"
                        "💬 如有紧急问题，请联系管理员",
                        parse_mode="HTML"
                    )
                except:
                    pass
            return  # 不继续处理
        
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
            # 发生错误时，为了避免阻塞用户操作，继续处理请求
            # SQLAlchemy异步上下文错误通常是临时的，不应该阻止用户使用
            if "greenlet_spawn" in str(e) or "await_only" in str(e):
                # 这是SQLAlchemy异步上下文错误，继续处理
                logger.warning("检测到SQLAlchemy异步上下文错误，跳过群组验证")
                return await handler(event, data)
            elif "no caption" in str(e) or "no text" in str(e):
                # 这是消息编辑的正常错误，继续处理
                return await handler(event, data)
            else:
                # 其他严重错误，拒绝访问
                try:
                    await event.answer(
                        "❌ 验证失败，请稍后重试。",
                        show_alert=True
                    )
                except:
                    # 如果连回复都失败了，直接返回
                    pass
                return
