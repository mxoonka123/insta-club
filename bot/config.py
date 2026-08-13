import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _resolve_db_path() -> Path:
    env_path = os.getenv("DB_PATH", "").strip()
    if env_path:
        return Path(env_path)

    data_dir = Path("/data")
    if data_dir.is_dir() and os.access(data_dir, os.W_OK):
        return data_dir / "profiles.db"
    return BASE_DIR / "profiles.db"


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = _resolve_db_path()
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")
CURATOR_USERNAME = os.getenv("CURATOR_USERNAME", "instaclub_curator").lstrip("@")
SEED_DEMO = os.getenv("SEED_DEMO", "").strip() in {"1", "true", "yes"}

BUSINESS_PRICE = os.getenv("BUSINESS_PRICE", "9 900 RSD / месяц")
PAYMENT_DETAILS = os.getenv(
    "PAYMENT_DETAILS",
    "После оплаты напишите куратору и нажмите «Я оплатил» в боте.\n"
    "Реквизиты и способ оплаты пришлёт куратор.",
)

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
