from datetime import datetime

from aiogram.types import Message

from bot.config import DB_PATH
from bot.database import get_user
from bot.keyboards import main_menu_keyboard, member_card_keyboard, welcome_keyboard


def format_date(value: str | None) -> str:
    if not value:
        return "—"
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
        try:
            return datetime.strptime(value[:19] if " " in value else value, fmt).strftime(
                "%d.%m.%Y"
            )
        except ValueError:
            continue
    return value


def member_card_text(user: dict) -> str:
    return (
        f"<b>{user.get('full_name') or 'Без имени'}</b>\n"
        f"{user.get('niche') or 'Ниша не указана'}\n"
        f"{user.get('city') or 'Город не указан'}\n"
        f"Цель: {user.get('goal') or '—'}"
    )


def profile_text(user: dict) -> str:
    return (
        "⚙ <b>Профиль</b>\n\n"
        f"Имя: {user.get('full_name') or '—'}\n"
        f"Город: {user.get('city') or '—'}\n"
        f"Ниша: {user.get('niche') or '—'}\n"
        f"Instagram: {user.get('instagram') or '—'}\n"
        f"Тариф: {user.get('tariff') or '—'}\n"
        f"Дата вступления: {format_date(user.get('joined_at'))}\n"
        f"Уведомления: {'вкл.' if user.get('notifications_enabled') else 'выкл.'}"
    )


async def require_member(message: Message) -> dict | None:
    if not message.from_user:
        return None
    user = get_user(DB_PATH, message.from_user.id)
    if user and user.get("is_member"):
        return user
    await message.answer(
        "Сначала пройдите онбординг — нажмите «Стать участником».",
        reply_markup=welcome_keyboard(),
    )
    return None


async def send_member_cards(message: Message, members: list[dict], empty_text: str) -> None:
    if not members:
        await message.answer(empty_text, reply_markup=main_menu_keyboard())
        return

    for member in members:
        await message.answer(
            member_card_text(member),
            reply_markup=member_card_keyboard(
                member.get("instagram"),
                member.get("username"),
            ),
        )
