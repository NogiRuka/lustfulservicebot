from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.database.schema import Base
from app.config import DATABASE_URL_ASYNC


"""
Create an async engine.
Defaults to SQLite with aiosqlite driver if DATABASE_URL_ASYNC is not provided.
"""
engine = create_async_engine(DATABASE_URL_ASYNC)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables if they do not exist (for SQLite learning mode)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 初始化默认系统设置
    await init_default_settings()


async def init_default_settings() -> None:
    """初始化默认系统设置"""
    from app.database.business import get_system_setting, set_system_setting
    
    # 按优先级排序的默认设置
    default_settings = {
        # 优先级1：核心功能开关
        "bot_enabled": "true",
        "movie_request_enabled": "true",
        "content_submit_enabled": "true",
        "feedback_enabled": "true",
        "admin_panel_enabled": "true",
        "dev_changelog_enabled": "true",
        
        # 优先级2：系统配置项
        "system_enabled": "true",
        "page_size": "5"
    }
    
    # 设置类型映射
    setting_types = {
        "page_size": "integer",
        # 其他都是boolean类型
    }
    
    for key, value in default_settings.items():
        # 只有当设置不存在时才创建默认值
        existing_value = await get_system_setting(key)
        if existing_value is None:
            setting_type = setting_types.get(key, "boolean")
            await set_system_setting(
                key, value, setting_type, 
                f"系统默认设置 - {key}", 
                updater_id=None
            )
