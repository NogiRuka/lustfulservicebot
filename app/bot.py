import sys
import traceback
import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from loguru import logger

from app.middlewares import AntiFloodMiddleware, AddUser, UpdateLastAcivity, GroupVerificationMiddleware
from app.config import BOT_TOKEN, ADMINS_ID, SUPERADMIN_ID
from app.handlers.users import users_routers
from app.handlers.admins import admin_routers
from app.handlers.superadmins import superadmin_routers
from app.utils.filters import IsAdmin, ChatTypeFilter, HasRole
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN
from app.database.db import init_db

# ===== 日志与调度器 =====
# 使用内存存储（演示/学习用，生产可替换为 Redis 等）
storage = MemoryStorage()
dp = Dispatcher(
    storage=storage
)  # 创建调度器实例

os.makedirs("./logs", exist_ok=True)
logger.add("./logs/errors.log", enqueue=True, rotation="1 week", level="ERROR")
logger.add("./logs/all.log", enqueue=True, rotation="1 week", level="DEBUG")
logger.add(sys.stdout, level="DEBUG")  # 控制台输出DEBUG日志

# ===== 机器人实例 =====
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# ===== 路由：管理（含超管） =====
for router in admin_routers:
    router.message.filter(ChatTypeFilter(chat_type=["private"]))
    router.message.filter(
        HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN])
    )
    dp.include_router(router)

# ===== 路由：超管（唯一） =====
for router in superadmin_routers:
    router.message.filter(ChatTypeFilter(chat_type=["private"]))
    router.message.filter(
        HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_SUPERADMIN])
    )
    dp.include_router(router)

# ===== 路由：用户（通用） =====
for router in users_routers:
    # 移除私聊限制，允许在群组中响应某些命令（如/start）
    # router.message.filter(ChatTypeFilter(chat_type=["private"]))
    dp.include_router(router)


async def main() -> None:
    """
    程序入口：初始化数据库、中间件并启动长轮询。
    """
    try:
        logger.info("机器人已启动...")
        logger.info(f"环境管理员ID：{ADMINS_ID}")
        logger.info(f"环境超管ID：{SUPERADMIN_ID}")
        # 确保数据库表存在（学习模式下自动创建）
        await init_db()
        dp.message.middleware(AntiFloodMiddleware())
        dp.message.middleware(AddUser())
        dp.message.middleware(UpdateLastAcivity())
        # 为回调查询添加群组验证中间件
        dp.callback_query.middleware(GroupVerificationMiddleware())
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"错误：{e}")
        traceback.format_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 异步运行入口
    asyncio.run(main())