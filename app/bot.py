import sys
import traceback
import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from loguru import logger

from app.middlewares import AntiFloodMiddleware, AddUser, UpdateLastAcivity, GroupVerificationMiddleware, BotStatusMiddleware
from app.config import BOT_TOKEN, ADMINS_ID, SUPERADMIN_ID, BOT_NICKNAME
from app.handlers.users import users_routers
from app.handlers.admins import admin_routers
from app.utils.filters import ChatTypeFilter, HasRole
from app.utils.roles import ROLE_ADMIN, ROLE_SUPERADMIN
from app.database.db import init_db, AsyncSessionLocal
from app.database.schema import DevChangelog
from sqlalchemy import select
from datetime import datetime

# ===== 日志与调度器 =====
# 使用内存存储（演示/学习用，生产可替换为 Redis 等）
storage = MemoryStorage()
dp = Dispatcher(
    storage=storage
)  # 创建调度器实例

os.makedirs("./logs", exist_ok=True)
logger.add("./logs/errors.log", enqueue=True, rotation="1 week", level="ERROR")
logger.add("./logs/all.log", enqueue=True, rotation="1 week", level="DEBUG")
# logger.add(sys.stdout, level="DEBUG")  # 控制台输出DEBUG日志

# ===== 机器人实例 =====
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# ===== 路由：管理（含超管） =====
for router in admin_routers:
    router.message.filter(ChatTypeFilter(chat_type=["private"]))
    router.message.filter(
        HasRole(superadmin_id=SUPERADMIN_ID, admins_id=ADMINS_ID, allow_roles=[ROLE_ADMIN, ROLE_SUPERADMIN])
    )
    dp.include_router(router)

# 超管路由现在包含在admin_routers中

# ===== 路由：用户（通用） =====
for router in users_routers:
    # 移除私聊限制，允许在群组中响应某些命令（如/start）
    # router.message.filter(ChatTypeFilter(chat_type=["private"]))
    dp.include_router(router)


# ===== 初始数据导入 =====
from app.config.initial_data import get_initial_changelog_data


async def _should_insert_initial_changelog(session) -> bool:
    """检查是否需要插入初始开发日志"""
    from sqlalchemy import exists
    
    stmt = select(exists().where(DevChangelog.id.isnot(None)))
    result = await session.execute(stmt)
    return not result.scalar()


async def _insert_initial_changelog(session) -> None:
    """插入初始开发日志"""
    logger.info("检测到首次启动，正在插入初始开发日志...")
    
    try:
        # 从配置文件获取初始数据
        changelog_data = get_initial_changelog_data()
        
        initial_changelog = DevChangelog(
            version=changelog_data["version"],
            title=changelog_data["title"],
            changelog_type=changelog_data["changelog_type"],
            created_by=SUPERADMIN_ID,
            content=changelog_data["content"]
        )
        
        session.add(initial_changelog)
        await session.commit()
        logger.success("✅ 初始开发日志插入成功！")
        
    except Exception as e:
        logger.error(f"插入开发日志失败: {e}")
        await session.rollback()
        raise


async def insert_initial_data_if_needed() -> None:
    """首次启动时插入初始数据（如开发日志）"""
    try:
        async with AsyncSessionLocal() as session:
            if await _should_insert_initial_changelog(session):
                await _insert_initial_changelog(session)
            else:
                logger.debug("开发日志已存在，跳过初始化")
                
    except Exception as e:
        logger.error(f"插入初始数据失败: {e}")
        # 不抛出异常，避免影响机器人启动


async def main() -> None:
    """
    程序入口：初始化数据库、中间件并启动长轮询。
    """
    try:
        logger.info(f"{BOT_NICKNAME}已启动...")
        # logger.info(f"环境管理员ID：{ADMINS_ID}")
        # logger.info(f"环境超管ID：{SUPERADMIN_ID}")
        # 确保数据库表存在（学习模式下自动创建）
        await init_db()
        
        # 首次启动时自动插入初始数据
        await insert_initial_data_if_needed()
        # 机器人状态检查中间件（最高优先级）
        dp.message.middleware(BotStatusMiddleware())
        dp.callback_query.middleware(BotStatusMiddleware())
        
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