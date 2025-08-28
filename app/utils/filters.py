from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.database.users import get_busy
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN


class ChatTypeFilter(BaseFilter):
    """聊天类型过滤器：只处理指定类型的聊天。"""

    def __init__(self, chat_type: Union[str, list]) -> None:
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type


class IsBusyFilter(BaseFilter):
    """用户忙碌过滤器：忙碌时不处理消息。"""

    async def __call__(self, message: Message) -> bool:
        return not await get_busy(message.from_user.id)


class IsCommand(BaseFilter):
    """命令过滤器：过滤以 / 开头的消息。"""

    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        if message.text.startswith("/"):
            return False
        else:
            return True


class IsAdmin(BaseFilter):
    """管理员过滤器：仅放行在管理员列表中的用户。"""

    def __init__(self, ADMINS_ID: list) -> None:
        self.admins = ADMINS_ID

    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in self.admins:
            return True
        else:
            return False


class HasRole(BaseFilter):
    """角色过滤器：根据用户在环境变量名单或数据库角色进行判定。

    简化实现：
    - 如果配置了 ADMINS_ID，则仍旧兼容旧逻辑用于管理员与超管。
    - 对于超管，仅允许唯一的 ID（ENV: SUPERADMIN_ID）。
    - 未来可扩展为从数据库读取用户角色。
    """

    def __init__(self, superadmin_id: int | None = None, admins_id: list[int] | None = None, allow_roles: list[str] | None = None) -> None:
        self.superadmin_id = superadmin_id
        self.admins_id = admins_id or []
        self.allow_roles = set(allow_roles or [])

    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id

        # 超管判定（唯一）
        if ROLE_SUPERADMIN in self.allow_roles:
            if self.superadmin_id is not None and user_id == self.superadmin_id:
                return True

        # 管理员与以上
        if ROLE_ADMIN in self.allow_roles or ROLE_SUPERADMIN in self.allow_roles:
            if user_id in self.admins_id:
                return True

        # 普通用户
        if not self.allow_roles or "user" in self.allow_roles:
            return True

        return False
