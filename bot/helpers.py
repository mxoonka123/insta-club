from datetime import datetime

from aiogram.types import Message

from bot.config import DB_PATH
from bot.database import STATUS_ACTIVE, STATUS_PENDING, STATUS_REJECTED, get_user
from bot.keyboards import (
    main_menu_keyboard,
    member_card_keyboard,
    pending_keyboard,
    welcome_keyboard,
)
from bot import texts


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


def is_active_member(user: dict | None) -> bool:
    return bool(user and user.get("is_member") and user.get("status") == STATUS_ACTIVE)


def status_label(user: dict) -> str:
    status = user.get("status")
    if status == STATUS_ACTIVE:
        return "активный участник"
    if status == STATUS_PENDING:
        if user.get("payment_claimed_at"):
            return "оплата на проверке"
        return "заявка ожидает оплаты / проверки"
    if status == STATUS_REJECTED:
        return "заявка отклонена"
    return "анкета не завершена"


def application_card(user: dict) -> str:
    username = f"@{user['username']}" if user.get("username") else "—"
    paid = format_date(user.get("payment_claimed_at")) if user.get("payment_claimed_at") else "ещё нет"
    return (
        "<b>Заявка в INSTA CLUB</b>\n"
        f"ID: <code>{user.get('telegram_id')}</code>\n"
        f"Username: {username}\n"
        f"Имя: {user.get('full_name') or '—'}\n"
        f"Город: {user.get('city') or '—'}\n"
        f"Ниша: {user.get('niche') or '—'}\n"
        f"Instagram: {user.get('instagram') or '—'}\n"
        f"Цель: {user.get('goal') or '—'}\n"
        f"Статус: {status_label(user)}\n"
        f"Оплата отмечена: {paid}"
    )


def member_card_text(user: dict) -> str:
    lines = [
        f"<b>{user.get('full_name') or 'Без имени'}</b>",
        f"{user.get('niche') or 'Ниша не указана'}",
        f"{user.get('city') or 'Город не указан'}",
        f"Цель: {user.get('goal') or '—'}",
    ]
    if user.get("intro"):
        lines.append("")
        lines.append(user["intro"])
    return "\n".join(lines)


def profile_text(user: dict) -> str:
    return (
        "⚙ <b>Профиль</b>\n\n"
        f"Имя: {user.get('full_name') or '—'}\n"
        f"Город: {user.get('city') or '—'}\n"
        f"Ниша: {user.get('niche') or '—'}\n"
        f"Instagram: {user.get('instagram') or '—'}\n"
        f"Статус: {status_label(user)}\n"
        f"Тариф: {user.get('tariff') or '—'}\n"
        f"Оплачен до: {format_date(user.get('tariff_until'))}\n"
        f"Дата вступления: {format_date(user.get('joined_at'))}\n"
        f"Уведомления: {'вкл.' if user.get('notifications_enabled') else 'выкл.'}"
    )


async def require_member(message: Message) -> dict | None:
    if not message.from_user:
        return None
    user = get_user(DB_PATH, message.from_user.id)
    if is_active_member(user):
        return user

    if user and user.get("status") == STATUS_PENDING:
        await message.answer(texts.PENDING_ACCESS, reply_markup=pending_keyboard())
        return None

    if user and user.get("status") == STATUS_REJECTED:
        await message.answer(texts.REJECTED, reply_markup=pending_keyboard())
        return None

    await message.answer(
        "Сначала подайте заявку — нажмите «Стать участником».",
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
