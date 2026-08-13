from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_IDS, DB_PATH
from bot.database import (
    admin_stats,
    approve_member,
    find_members,
    get_user,
    list_pending_applications,
    reject_member,
    renew_subscription,
    revoke_member,
)
from bot.helpers import application_card
from bot.keyboards import (
    after_approval_keyboard,
    application_admin_keyboard,
    main_menu_keyboard,
    member_admin_keyboard,
    pending_keyboard,
)
from bot import texts

router = Router(name="admin")


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMIN_IDS)


def _command_args(message: Message, command: CommandObject | None = None) -> str:
    if command and command.args:
        return command.args.strip()
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2:
        return parts[1].strip()
    return ""


def _extract_id(message: Message, command: CommandObject | None = None) -> int | None:
    raw = _command_args(message, command)
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return int(digits)
    return None


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Команда доступна только администраторам.")
        return

    stats = admin_stats(DB_PATH)
    lines = [
        "<b>Админ-панель INSTA CLUB</b>",
        f"Активных участников: {stats['total']}",
        f"Заявок на проверке: {stats['pending']}",
        f"Из них отметили оплату: {stats['paid_claims']}",
        "",
        "Команды:",
        "/applications — список заявок",
        "/find имя — найти участника",
        "/approve ID — одобрить",
        "/reject ID — отклонить заявку",
        "/kick ID — закрыть доступ",
        "/renew ID — продлить на 30 дней",
        "",
        "<b>По городам</b>",
    ]
    for row in stats["by_city"][:8]:
        lines.append(f"• {row['city']}: {row['c']}")

    lines.append("")
    lines.append("<b>По нишам</b>")
    for row in stats["by_niche"][:8]:
        lines.append(f"• {row['niche']}: {row['c']}")

    await message.answer("\n".join(lines))


@router.message(Command("applications"))
async def applications_list(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Команда доступна только администраторам.")
        return

    apps = list_pending_applications(DB_PATH)
    if not apps:
        await message.answer("Новых заявок нет.")
        return

    await message.answer(f"Заявок: {len(apps)}")
    for app in apps:
        await message.answer(
            application_card(app),
            reply_markup=application_admin_keyboard(int(app["telegram_id"])),
        )


@router.message(Command("approve"))
async def approve_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Формат: /approve 123456789")
        return
    await _approve(message, user_id)


@router.message(Command("reject"))
async def reject_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Формат: /reject 123456789")
        return
    await _reject(message, user_id)


@router.message(Command("find"))
async def find_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    query = _command_args(message, command)
    if not query:
        await message.answer("Формат: /find Мария  или  /find 318427459")
        return

    members = find_members(DB_PATH, query)
    if not members:
        await message.answer(
            "Никого не нашли. Проверьте ID или имя.\n"
            "Пример: /find Людмила"
        )
        return

    await message.answer(f"Найдено: {len(members)}")
    for member in members:
        markup = member_admin_keyboard(int(member["telegram_id"]))
        await message.answer(application_card(member), reply_markup=markup)


@router.message(Command("kick"))
async def kick_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Формат: /kick 318427459")
        return
    await _kick(message, user_id)


@router.message(Command("renew"))
async def renew_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Формат: /renew 123456789")
        return

    user = renew_subscription(DB_PATH, user_id)
    if not user:
        await message.answer("Пользователь не найден.")
        return

    await message.answer(f"Подписка продлена: {user.get('full_name')} до {user.get('tariff_until')}")
    try:
        await message.bot.send_message(
            user_id,
            f"Подписка продлена до <b>{user.get('tariff_until')}</b>.",
            reply_markup=main_menu_keyboard(),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin:approve:"))
async def approve_callback(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int((callback.data or "").split(":")[-1])
    await callback.answer("Одобрено")
    if callback.message:
        await _approve(callback.message, user_id, edit=True)


@router.callback_query(F.data.startswith("admin:reject:"))
async def reject_callback(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int((callback.data or "").split(":")[-1])
    await callback.answer("Отклонено")
    if callback.message:
        await _reject(callback.message, user_id, edit=True)


@router.callback_query(F.data.startswith("admin:kick:"))
async def kick_callback(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int((callback.data or "").split(":")[-1])
    await callback.answer("Доступ закрыт")
    if callback.message:
        await _kick(callback.message, user_id, edit=True)


async def _approve(message: Message, user_id: int, edit: bool = False) -> None:
    before = get_user(DB_PATH, user_id)
    if not before:
        await message.answer("Пользователь не найден.")
        return

    user = approve_member(DB_PATH, user_id)
    text = f"✅ Одобрено\n\n{application_card(user or before)}"
    if edit:
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text)
    else:
        await message.answer(text)

    try:
        await message.bot.send_message(
            user_id,
            texts.APPROVED,
            reply_markup=main_menu_keyboard(),
        )
        await message.bot.send_message(
            user_id,
            "Быстрые действия:",
            reply_markup=after_approval_keyboard(),
        )
    except Exception:
        await message.answer("Пользователь одобрен, но сообщение ему не отправилось.")


async def _reject(message: Message, user_id: int, edit: bool = False) -> None:
    before = get_user(DB_PATH, user_id)
    if not before:
        await message.answer("Пользователь не найден.")
        return

    user = reject_member(DB_PATH, user_id)
    text = f"❌ Отклонено\n\n{application_card(user or before)}"
    if edit:
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text)
    else:
        await message.answer(text)

    try:
        await message.bot.send_message(user_id, texts.REJECTED)
    except Exception:
        pass


async def _kick(message: Message, user_id: int, edit: bool = False) -> None:
    before = get_user(DB_PATH, user_id)
    if not before:
        await message.answer("Пользователь не найден.")
        return

    user = revoke_member(DB_PATH, user_id)
    text = f"🚫 Доступ закрыт\n\n{application_card(user or before)}"
    if edit:
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text)
    else:
        await message.answer(text)

    try:
        await message.bot.send_message(
            user_id,
            texts.KICKED,
            reply_markup=pending_keyboard(),
        )
    except Exception:
        await message.answer("Доступ закрыт, но сообщение пользователю не отправилось.")
