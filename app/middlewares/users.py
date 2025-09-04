from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from app.database.users import add_user, update_last_acitivity, update_user_stats, update_user_behavior
from app.utils.user_info_collector import collect_and_store_user_info


class AddUser(BaseMiddleware):
    """
    用户入库中间件：
    - 首次交互时将用户详细信息写入数据库（幂等）。
    - 收集IP地址、设备信息、地理位置等详细数据。
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # 尝试获取用户的详细信息
        ip_address = None
        user_agent = None
        
        # 从Telegram获取用户信息（如果可用）
        telegram_user = event.from_user
        
        # 使用完整的用户信息收集系统
        try:
            await collect_and_store_user_info(
                telegram_user=telegram_user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            # 如果详细信息收集失败，回退到基础用户创建
            await add_user(event.chat.id, event.chat.full_name, event.chat.username)

        return await handler(event, data)


class UpdateLastAcivity(BaseMiddleware):
    """
    活跃时间更新中间件：
    - 每次消息到达时更新用户的最近活跃时间。
    - 更新用户统计信息（消息数、命令数）。
    - 分析用户行为模式。
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        from datetime import datetime
        
        # 更新最后活动时间
        await update_last_acitivity(event.chat.id)
        
        # 更新消息统计
        await update_user_stats(event.chat.id, 'messages')
        
        # 如果是命令消息，更新命令统计
        if event.text and event.text.startswith('/'):
            await update_user_stats(event.chat.id, 'commands')
            
            # 更新最后使用的命令
            command = event.text.split()[0] if event.text else None
            if command:
                await update_user_behavior(event.chat.id, {'last_command': command})
        
        # 更新最活跃时间
        current_hour = datetime.now().hour
        await update_user_behavior(event.chat.id, {'most_active_hour': current_hour})

        return await handler(event, data)
