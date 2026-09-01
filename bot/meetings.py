from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from bot.database import count_rsvps

try:
    BELGRADE = ZoneInfo("Europe/Belgrade")
except Exception:
    BELGRADE = timezone(timedelta(hours=2))

MONTHS = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


def parse_local_datetime(date_text: str, time_text: str) -> datetime | None:
    try:
        parts = date_text.replace("/", ".").split(".")
        if len(parts) != 3 or len(parts[2]) != 4:
            return None
        day, month, year = [int(part) for part in parts]
        if year < 2020:
            return None
        hour, minute = [int(part) for part in time_text.replace(".", ":").split(":")]
        local = datetime(year, month, day, hour, minute, tzinfo=BELGRADE)
        return local.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def parse_stored(starts_at: str) -> datetime:
    return datetime.fromisoformat(starts_at[:19])


def format_when(starts_at: str) -> str:
    utc = parse_stored(starts_at).replace(tzinfo=timezone.utc)
    local = utc.astimezone(BELGRADE)
    return f"{local.day} {MONTHS[local.month - 1]}, {local.strftime('%H:%M')}"


def format_place(meeting: dict) -> str:
    if meeting.get("format") == "online":
        return "💻 ONLINE"
    city = meeting.get("city") or "—"
    return f"📍 {city} — офлайн"


def format_meeting(meeting: dict, db_path) -> str:
    taken = count_rsvps(db_path, int(meeting["id"]))
    seats = meeting.get("seats")
    seats_line = f"Мест: {taken}" if seats is None else f"Мест: {taken} / {seats}"
    place = format_place(meeting)
    extra = ""
    if meeting.get("format") == "online":
        extra = "\nВстречаемся всем INSTA CLUB,\nнезависимо от города.\n"

    return (
        "<b>СЛЕДУЮЩАЯ ВСТРЕЧА ✦</b>\n\n"
        f"{place}\n"
        f"{extra}\n"
        f"Тема: {meeting.get('topic')}\n"
        f"Когда: {format_when(meeting['starts_at'])}\n"
        f"{seats_line}"
    )


def format_archive_item(meeting: dict, db_path) -> str:
    taken = count_rsvps(db_path, int(meeting["id"]))
    return (
        f"{format_when(meeting['starts_at'])} · {format_place(meeting)}\n"
        f"{meeting.get('topic')} · было {taken} уч."
    )


def format_announce(meeting: dict) -> str:
    place = format_place(meeting)
    extra = ""
    if meeting.get("format") == "online":
        extra = "\nВстречаемся всем INSTA CLUB, независимо от города.\n"
    return (
        "<b>Новая встреча INSTA CLUB ✦</b>\n\n"
        f"{place}\n"
        f"{extra}\n"
        f"Тема: {meeting.get('topic')}\n"
        f"Когда: {format_when(meeting['starts_at'])}\n\n"
        "Откройте «📅 Встречи клуба» → «Ближайшая встреча», чтобы записаться."
    )
