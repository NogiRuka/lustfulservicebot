import sys
import traceback

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from loguru import logger


from middlewares import AntiFloodMiddleware, AddUser, UpdateLastAcivity
from database.db import init_db
from config import BOT_TOKEN

# Add a new logger with the desired configuration
# Set up logging
storage = MemoryStorage()  # Initializing in-memory storage for the bot's dispatcher
dp = Dispatcher(
    storage=storage
)  # Creating a dispatcher instance with the memory storage
router = Router()

logger.add("requests.log", enqueue=True, rotation="1 week")

# Initializing the bot instance with the token and default settings
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp.include_router(router)


async def main() -> None:
    # Starting the long-polling mechanism for the bot with the dispatcher
    try:
        logger.info("Bot started...")
        await init_db()
        dp.message.middleware(AntiFloodMiddleware())
        dp.message.middleware(AddUser())
        dp.message.middleware(UpdateLastAcivity())
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error: {e}")
        traceback.format_exc()
        sys.exit(1)
