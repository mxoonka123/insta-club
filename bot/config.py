import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_FILENAME = "instaclub.db"
LEGACY_DB_FILENAME = "profiles.db"


def is_railway() -> bool:
    return bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))


def volume_mount_path() -> Path | None:
    raw = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
    return Path(raw) if raw else None


def _pick_sqlite_file(directory: Path) -> Path:
    legacy = directory / LEGACY_DB_FILENAME
    current = directory / DB_FILENAME
    if legacy.exists() and not current.exists():
        return legacy
    return current


def _resolve_db_path() -> Path:
    env_path = os.getenv("DB_PATH", "").strip()
    if env_path:
        return Path(env_path)

    volume = volume_mount_path()
    if volume:
        return _pick_sqlite_file(volume)

    data_dir = Path("/data")
    if data_dir.is_dir() and os.access(data_dir, os.W_OK):
        return _pick_sqlite_file(data_dir)

    if is_railway():
        return data_dir / DB_FILENAME

    return BASE_DIR / DB_FILENAME


def db_is_persistent(db_path: Path | None = None) -> bool:
    """False on Railway when the SQLite file is not on a Volume."""
    path = (db_path or _resolve_db_path()).expanduser()
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path

    if not is_railway():
        return True

    volume = volume_mount_path()
    if volume:
        try:
            return resolved.is_relative_to(volume.expanduser().resolve())
        except OSError:
            return False

    for parent in [resolved.parent, *resolved.parents]:
        if parent == parent.parent:
            break
        if str(parent) in {"/", "/app", "/usr", "/home", "/opt", "/tmp"}:
            continue
        if os.path.ismount(str(parent)):
            return True
    return False


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = _resolve_db_path()
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")
CURATOR_USERNAME = os.getenv("CURATOR_USERNAME", "instaclub_curator").lstrip("@")
SEED_DEMO = os.getenv("SEED_DEMO", "").strip() in {"1", "true", "yes"}

BUSINESS_PRICE = os.getenv("BUSINESS_PRICE", "19 € / месяц")
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
