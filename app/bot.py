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


async def insert_initial_data_if_needed() -> None:
    """首次启动时插入初始数据（如开发日志）"""
    try:
        async with AsyncSessionLocal() as session:
            # 检查是否已有开发日志
            stmt = select(DevChangelog.id).limit(1)
            result = await session.execute(stmt)
            
            if not result.fetchone():
                logger.info("检测到首次启动，正在插入初始开发日志...")
                
                # 创建初始开发日志
                initial_changelog = DevChangelog(
                    version="v1.0.0",
                    title="🎉 桜色服务助手首次发布",
                    changelog_type="feature",
                    created_by=SUPERADMIN_ID,
                    content="""🌸 **桜色服务助手 v1.0.0 正式发布！**

## ✨ **核心功能**

### 🎯 **代发消息系统**
- ✅ 支持发送消息给指定用户 (`/su`)
- ✅ 支持发送消息到频道 (`/sc`)
- ✅ 支持发送消息到群组 (`/sg`)
- ✅ 智能编辑/回复降级机制
- ✅ 完整的消息记录和追踪

### 📬 **回复追踪系统**
- ✅ 自动监听用户回复
- ✅ 实时通知所有管理员
- ✅ 完整的对话历史记录
- ✅ 已读状态管理
- ✅ 反馈回复特殊处理

### 👥 **用户管理系统**
- ✅ 三级权限控制（用户/管理员/超管）
- ✅ 动态权限分配
- ✅ 用户信息自动收集
- ✅ 活跃度统计

### 💬 **反馈系统**
- ✅ 用户反馈收集
- ✅ 管理员回复功能
- ✅ 反馈状态跟踪
- ✅ 分类管理

### 📝 **内容管理**
- ✅ 求片功能
- ✅ 内容投稿
- ✅ 审核流程
- ✅ 分类管理
- ✅ 状态跟踪

### 🛠️ **系统管理**
- ✅ 灵活的系统设置
- ✅ 功能开关控制
- ✅ 图片库管理
- ✅ 开发日志管理
- ✅ 完整的日志记录

## 🔧 **技术特性**

### 🏗️ **架构设计**
- ✅ 基于 aiogram 3.x 异步框架
- ✅ 模块化路由设计
- ✅ 中间件系统
- ✅ 状态管理

### 🗄️ **数据库**
- ✅ SQLAlchemy ORM
- ✅ 异步数据库操作
- ✅ 完整的数据模型
- ✅ 自动表创建

### 📊 **日志系统**
- ✅ loguru 日志框架
- ✅ 文件轮转
- ✅ 多级别日志
- ✅ 调试支持

### 🔒 **安全性**
- ✅ 权限验证
- ✅ 角色检查
- ✅ 操作日志
- ✅ 错误处理

---

**感谢使用桜色服务助手！这是一个里程碑式的版本，标志着项目的正式发布。** 🎉✨🚀"""
                )
                
                session.add(initial_changelog)
                await session.commit()
                
                logger.success("✅ 初始开发日志插入成功！")
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