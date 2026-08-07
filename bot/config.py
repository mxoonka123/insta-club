import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "profiles.db")))
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")
CURATOR_USERNAME = os.getenv("CURATOR_USERNAME", "instaclub_curator").lstrip("@")

_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = {
    int(item.strip())
    for item in _admin_raw.split(",")
    if item.strip().isdigit()
}

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не задан. Скопируйте .env.example в .env и укажите токен бота."
    )
