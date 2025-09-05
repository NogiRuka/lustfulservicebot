from dotenv import load_dotenv
import os
from pathlib import Path

# Always load .env from project root (two levels up from this file)
_project_root = Path(__file__).resolve().parents[2]
_root_env = _project_root / ".env"
if _root_env.exists():
    load_dotenv(dotenv_path=_root_env, override=True, encoding="utf-8")
else:
    # Fallback: load from current working directory
    load_dotenv(override=True, encoding="utf-8")

BOT_NICKNAME = os.getenv("BOT_NICKNAME")
BOT_NAME = os.getenv("BOT_NAME")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Safely parse admins list (allow empty)
_admins_raw = os.getenv("ADMINS_ID", "").strip()
ADMINS_ID = (
    [int(x) for x in _admins_raw.split(",") if x.strip().isdigit()]
    if _admins_raw
    else []
)

# 超管（唯一）：如果未设置则为 None
_superadmin_raw = os.getenv("SUPERADMIN_ID", "").strip()
SUPERADMIN_ID = int(_superadmin_raw) if _superadmin_raw.isdigit() else None

# 群组设置：从环境变量读取允许的群组
GROUP = os.getenv("GROUP", "").strip()

# 同步频道设置：用于同步求片和投稿内容（支持多个频道，用逗号分隔）
_sync_channels_raw = os.getenv("SYNC_CHANNELS", "").strip()
SYNC_CHANNELS = (
    [x.strip() for x in _sync_channels_raw.split(",") if x.strip()]
    if _sync_channels_raw
    else []
)

# 兼容旧配置
_sync_channel_raw = os.getenv("SYNC_CHANNEL", "").strip()
if _sync_channel_raw and not SYNC_CHANNELS:
    SYNC_CHANNELS = [_sync_channel_raw]

# Default to local SQLite (async) if not provided
# 默认使用相对路径的 SQLite 数据库（相对于当前运行目录）
_default_sqlite_url = "sqlite+aiosqlite:///./db/lustfulservice.db"
DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC", _default_sqlite_url)

# 分页配置常量
REVIEW_PAGE_SIZE = 3  # 审核列表每页显示的项目数量
BROWSE_PAGE_SIZE = 5  # 浏览列表每页显示的项目数量
ADVANCED_BROWSE_PAGE_SIZE = 10  # 高级浏览每页显示的项目数量
ADVANCED_BROWSE_LARGE_PAGE_SIZE = 15  # 高级浏览大页面每页显示的项目数量
SUBMISSION_PAGE_SIZE = 5  # 投稿列表每页显示的项目数量
CATEGORY_PAGE_SIZE = 5  # 分类列表每页显示的项目数量
SETTINGS_PAGE_SIZE = 8  # 设置列表每页显示的项目数量