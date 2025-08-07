from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS_ID = list(map(int, str(os.getenv("ADMINS_ID")).split(",")))
DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC")