import sys
import traceback
import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from loguru import logger

from app.middlewares import AntiFloodMiddleware, AddUser, UpdateLastAcivity
from app.config import BOT_TOKEN, ADMINS_ID
from app.handlers.users import users_routers
from app.handlers.admins import admin_routers
from app.utils.filters import IsAdmin, ChatTypeFilter

# Add a new logger with the desired configuration
# Set up logging
storage = MemoryStorage()  # Initializing in-memory storage for the bot's dispatcher
dp = Dispatcher(
    storage=storage
)  # Creating a dispatcher instance with the memory storage

os.makedirs("./logs", exist_ok=True)
logger.add("./logs/errors.log", enqueue=True, rotation="1 week", level="ERROR")
logger.add("./logs/all.log", enqueue=True, rotation="1 week")

# Initializing the bot instance with the token and default settings
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Include all admin routers
for router in admin_routers:
    router.message.filter(ChatTypeFilter(chat_type=["private"]))
    router.message.filter(IsAdmin(ADMINS_ID))
    dp.include_router(router)

# Include all user routers
for router in users_routers:
    router.message.filter(ChatTypeFilter(chat_type=["private"]))
    dp.include_router(router)


async def main() -> None:
    # Starting the long-polling mechanism for the bot with the dispatcher
    try:
        logger.info("Bot started...")
        dp.message.middleware(AntiFloodMiddleware())
        dp.message.middleware(AddUser())
        dp.message.middleware(UpdateLastAcivity())
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error: {e}")
        traceback.format_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Running the main function asynchronously using asyncio
    asyncio.run(main())