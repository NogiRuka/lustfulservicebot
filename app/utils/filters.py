from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.database.users import get_busy


# Filter to answer type of chats
class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Union[str, list]) -> None:
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type


# Do not handle if user is busy
class IsBusyFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return not await get_busy(message.from_user.id)


# Do not handle if user sending commands
class IsCommand(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        if message.text.startswith("/"):
            return False
        else:
            return True


# Is admin
class IsAdmin(BaseFilter):
    def __init__(self, ADMINS_ID: list) -> None:
        self.admins = ADMINS_ID

    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in self.admins:
            return True
        else:
            return False
