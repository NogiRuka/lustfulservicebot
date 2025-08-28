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

# Default to local SQLite (async) if not provided
# 默认使用相对路径的 SQLite 数据库（相对于当前运行目录）
_default_sqlite_url = "sqlite+aiosqlite:///./jessy.db"
DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC", _default_sqlite_url)