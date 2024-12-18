import asyncio

from aiogram import types, F
from aiogram.filters import CommandStart, Command
from loguru import logger

from utils.filters import IsBusyFilter, ChatTypeFilter, IsCommand
from database.users import get_busy, set_busy
from bot import bot, router


# Starting bot
@router.message(ChatTypeFilter(chat_type=["private"]), IsBusyFilter(), CommandStart())
async def start(msg: types.Message):
    # Sending a message to the user to initiate a conversation about their interests
    await bot.send_message(msg.from_user.id, "Hello")


# Show help info
@router.message(ChatTypeFilter(chat_type=["private"]), Command("help"))
async def help_handler(msg: types.Message):
    help_message = "<b>🤖 Bot name</b> can help with ..."

    await bot.send_message(msg.from_user.id, help_message)


# Handling regular messages
@router.message(
    F.text, ChatTypeFilter(chat_type=["private"]), IsCommand(), IsBusyFilter()
)
async def message(msg: types.Message):
    # If user is busy, notify them and wait for 5 seconds
    if await get_busy(msg.from_user.id):
        await bot.send_message(
            msg.from_user.id, "Please wait, until I process your last request"
        )
        await asyncio.sleep(5)
        return

    try:
        await set_busy(msg.from_user.id, True)
        # Sending a message to the user to initiate a conversation about their interests
        await bot.send_message(msg.from_user.id, msg.text)
    except Exception as e:
        logger.error(e)
        # Adding user message to the database
    finally:
        # Resetting user's busy status to False (False - means user is not busy)
        await set_busy(msg.from_user.id, False)
