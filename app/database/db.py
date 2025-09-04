import os
from pathlib import Path
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
    # 自动创建数据库目录
    if DATABASE_URL_ASYNC.startswith('sqlite'):
        # 从数据库URL中提取文件路径
        db_path = DATABASE_URL_ASYNC.replace('sqlite+aiosqlite:///', '')
        if db_path.startswith('./'):
            db_path = db_path[2:]  # 移除 './'
        
        # 创建数据库文件的目录
        db_dir = Path(db_path).parent
        if db_dir != Path('.'):
            os.makedirs(db_dir, exist_ok=True)
            print(f"数据库目录已创建: {db_dir}")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 初始化默认系统设置
    await init_default_settings()
    
    # 初始化默认类型数据
    await init_default_categories()


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


async def init_default_categories() -> None:
    """初始化默认类型数据"""
    from app.database.business import get_all_movie_categories, create_movie_category
    
    # 检查是否已有类型数据
    existing_categories = await get_all_movie_categories(active_only=False)
    if existing_categories:
        return  # 如果已有数据，保持现有数据不变
    
    # 默认类型数据（适用于求片和投稿）
    # 注意：这些是新数据库的默认类型，现有数据库已有类型数据会被保留
    default_categories = [
        {
            "name": "电影",
            "description": "院线电影、网络电影等",
            "sort_order": 1
        },
        {
            "name": "剧集",
            "description": "电视剧、网剧等连续剧集",
            "sort_order": 2
        },
        {
            "name": "动漫",
            "description": "动画片、动漫剧集等",
            "sort_order": 3
        },
        {
            "name": "国产🔞",
            "description": "国产成人内容",
            "sort_order": 4
        },
        {
            "name": "日韩🔞",
            "description": "日韩成人内容",
            "sort_order": 5
        },
        {
            "name": "欧美🔞",
            "description": "欧美成人内容",
            "sort_order": 6
        }
    ]
    
    # 创建默认类型（使用系统用户ID 0）
    for category_data in default_categories:
        await create_movie_category(
            name=category_data["name"],
            description=category_data["description"],
            creator_id=0,  # 系统创建
            sort_order=category_data["sort_order"]
        )
