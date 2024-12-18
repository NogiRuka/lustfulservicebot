from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS_ID = list(map(int, str(os.getenv("ADMINS_ID")).split(",")))
BASE_DIR = Path(
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))
)
DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC")
