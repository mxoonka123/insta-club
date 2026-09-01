from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_IDS, DB_PATH
from bot.database import (
    admin_stats,
    approve_member,
    find_members,
    get_user,
    list_all_users,
    list_pending_applications,
    reject_member,
    renew_subscription,
    revoke_member,
)
from bot.filters import IsAdmin
from bot.helpers import application_card, home_keyboard_for
from bot.keyboards import (
    BTN_ADMIN_APPS,
    BTN_ADMIN_CREATE,
    BTN_ADMIN_EXIT,
    BTN_ADMIN_FIND,
    BTN_ADMIN_MEETINGS,
    BTN_ADMIN_MEMBERS,
    BTN_ADMIN_STATS,
    admin_panel_keyboard,
    admin_user_actions_keyboard,
    after_approval_keyboard,
    application_admin_keyboard,
    main_menu_keyboard,
    welcome_keyboard,
)
from bot.states import AdminFind
from bot import texts

router = Router(name="admin")

ADMIN_ENTRY_TEXTS = {"админ", "admin"}
ADMIN_MENU_BUTTONS = {
    BTN_ADMIN_APPS,
    BTN_ADMIN_MEMBERS,
    BTN_ADMIN_FIND,
    BTN_ADMIN_MEETINGS,
    BTN_ADMIN_CREATE,
    BTN_ADMIN_STATS,
    BTN_ADMIN_EXIT,
}


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


def _is_admin_word(text: str | None) -> bool:
    return (text or "").strip().lower() in ADMIN_ENTRY_TEXTS


def _panel_text() -> str:
    stats = admin_stats(DB_PATH)
    lines = [
        "<b>Админ-панель INSTA CLUB</b>",
        "",
        f"Активных участников: {stats['total']}",
        f"Заявок на проверке: {stats['pending']}",
        f"Из них отметили оплату: {stats['paid_claims']}",
        f"Всего записей в базе: {stats['all_records']}",
        "",
        "Кнопки внизу — заявки, участники, поиск, встречи.",
        "Чтобы выйти, нажмите «← Выйти из админки».",
    ]
    if stats["by_city"]:
        lines.append("")
        lines.append("<b>По городам</b>")
        for row in stats["by_city"][:8]:
            lines.append(f"• {row['city']}: {row['c']}")
    if stats["by_niche"]:
        lines.append("")
        lines.append("<b>По нишам</b>")
        for row in stats["by_niche"][:8]:
            lines.append(f"• {row['niche']}: {row['c']}")
    return "\n".join(lines)


async def _open_panel(message: Message, state: FSMContext | None = None) -> None:
    if state:
        await state.clear()
    await message.answer(_panel_text(), reply_markup=admin_panel_keyboard())


@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Админка доступна только организаторам.")
        return
    await _open_panel(message, state)


@router.message(IsAdmin(), F.text.func(_is_admin_word))
async def admin_word(message: Message, state: FSMContext) -> None:
    await _open_panel(message, state)


@router.message(IsAdmin(), F.text == BTN_ADMIN_STATS)
async def admin_stats_button(message: Message, state: FSMContext) -> None:
    await _open_panel(message, state)


@router.message(IsAdmin(), F.text == BTN_ADMIN_EXIT)
async def admin_exit(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = get_user(DB_PATH, message.from_user.id) if message.from_user else None
    await message.answer(
        "Админка закрыта.\nЧтобы открыть снова, напишите: админ",
        reply_markup=home_keyboard_for(user),
    )


@router.message(IsAdmin(), F.text == BTN_ADMIN_APPS)
async def admin_apps_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _show_applications(message)


@router.message(IsAdmin(), F.text == BTN_ADMIN_MEMBERS)
async def admin_members_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _show_members(message)


@router.message(IsAdmin(), F.text == BTN_ADMIN_FIND)
async def admin_find_button(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminFind.query)
    await message.answer(
        "Напишите имя, @ник, город или Telegram ID.\n"
        "Либо нажмите другую кнопку внизу, чтобы отменить поиск.",
        reply_markup=admin_panel_keyboard(),
    )


@router.message(IsAdmin(), F.text == BTN_ADMIN_MEETINGS)
async def admin_meetings_button_text(message: Message, state: FSMContext) -> None:
    await state.clear()
    from bot.handlers.events import _send_admin_meetings

    await _send_admin_meetings(message)


@router.message(IsAdmin(), F.text == BTN_ADMIN_CREATE)
async def admin_create_meeting_button(message: Message, state: FSMContext) -> None:
    from bot.handlers.events import _start_create_meeting

    await _start_create_meeting(message, state)


@router.message(AdminFind.query, IsAdmin(), F.text, ~F.text.startswith("/"))
async def admin_find_query(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if query in ADMIN_MENU_BUTTONS or _is_admin_word(query):
        return
    if len(query) < 2:
        await message.answer("Напишите имя, @ник или ID — минимум 2 символа.")
        return
    await state.clear()
    await _show_find_results(message, query)


@router.message(Command("members"))
async def members_list(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Команда доступна только администраторам.")
        return
    await _show_members(message)


@router.message(Command("applications"))
async def applications_list(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Команда доступна только администраторам.")
        return
    await _show_applications(message)


@router.message(Command("approve"))
async def approve_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Откройте заявки в админке и нажмите «Одобрить».")
        return
    await _approve(message, user_id)


@router.message(Command("reject"))
async def reject_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Откройте заявки в админке и нажмите «Отклонить».")
        return
    await _reject(message, user_id)


@router.message(Command("find"))
async def find_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    query = _command_args(message, command)
    if not query:
        await message.answer("В админке нажмите «🔎 Найти» и напишите имя или ID.")
        return
    await _show_find_results(message, query)


@router.message(Command("kick"))
async def kick_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Найдите человека в админке и нажмите «Закрыть доступ».")
        return
    await _kick(message, user_id)


@router.message(Command("renew"))
async def renew_command(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    user_id = _extract_id(message, command)
    if not user_id:
        await message.answer("Найдите человека в админке и нажмите «Продлить 30 дней».")
        return
    await _renew(message, user_id)


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


@router.callback_query(F.data.startswith("admin:renew:"))
async def renew_callback(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int((callback.data or "").split(":")[-1])
    await callback.answer("Продлено")
    if callback.message:
        await _renew(callback.message, user_id, edit=True)


async def _show_applications(message: Message) -> None:
    apps = list_pending_applications(DB_PATH)
    if not apps:
        await message.answer("Новых заявок нет.", reply_markup=admin_panel_keyboard())
        return
    await message.answer(f"Заявок: {len(apps)}", reply_markup=admin_panel_keyboard())
    for app in apps:
        await message.answer(
            application_card(app),
            reply_markup=application_admin_keyboard(int(app["telegram_id"])),
        )


async def _show_members(message: Message) -> None:
    members = list_all_users(DB_PATH)
    if not members:
        await message.answer(
            "В базе никого нет. После редеплоя данные могли сброситься.\n"
            "На Railway нужен Volume с путём /data и переменная "
            "DB_PATH=/data/profiles.db",
            reply_markup=admin_panel_keyboard(),
        )
        return

    await message.answer(
        f"В базе: {len(members)} (показаны последние записи).",
        reply_markup=admin_panel_keyboard(),
    )
    for member in members:
        await message.answer(
            application_card(member),
            reply_markup=admin_user_actions_keyboard(member),
        )


async def _show_find_results(message: Message, query: str) -> None:
    members = find_members(DB_PATH, query)
    if not members:
        stats = admin_stats(DB_PATH)
        await message.answer(
            "Этого человека сейчас нет в базе.\n\n"
            f"Всего записей: {stats['all_records']}\n"
            "После редеплоя SQLite могла обнулиться.",
            reply_markup=admin_panel_keyboard(),
        )
        return

    await message.answer(f"Найдено: {len(members)}", reply_markup=admin_panel_keyboard())
    for member in members:
        await message.answer(
            application_card(member),
            reply_markup=admin_user_actions_keyboard(member),
        )


async def _approve(message: Message, user_id: int, edit: bool = False) -> None:
    before = get_user(DB_PATH, user_id)
    if not before:
        await message.answer("Пользователь не найден.", reply_markup=admin_panel_keyboard())
        return

    user = approve_member(DB_PATH, user_id)
    text = f"✅ Одобрено\n\n{application_card(user or before)}"
    if edit:
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text, reply_markup=admin_panel_keyboard())
    else:
        await message.answer(text, reply_markup=admin_panel_keyboard())

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
        await message.answer("Пользователь не найден.", reply_markup=admin_panel_keyboard())
        return

    user = reject_member(DB_PATH, user_id)
    text = f"❌ Отклонено\n\n{application_card(user or before)}"
    if edit:
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text, reply_markup=admin_panel_keyboard())
    else:
        await message.answer(text, reply_markup=admin_panel_keyboard())

    try:
        await message.bot.send_message(
            user_id,
            texts.REJECTED,
            reply_markup=welcome_keyboard(),
        )
    except Exception:
        pass


async def _kick(message: Message, user_id: int, edit: bool = False) -> None:
    before = get_user(DB_PATH, user_id)
    if not before:
        await message.answer("Пользователь не найден.", reply_markup=admin_panel_keyboard())
        return

    user = revoke_member(DB_PATH, user_id)
    text = f"🚫 Доступ закрыт\n\n{application_card(user or before)}"
    if edit:
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text, reply_markup=admin_panel_keyboard())
    else:
        await message.answer(text, reply_markup=admin_panel_keyboard())

    try:
        await message.bot.send_message(
            user_id,
            texts.KICKED,
            reply_markup=welcome_keyboard(),
        )
    except Exception:
        await message.answer("Доступ закрыт, но сообщение пользователю не отправилось.")


async def _renew(message: Message, user_id: int, edit: bool = False) -> None:
    user = renew_subscription(DB_PATH, user_id)
    if not user:
        await message.answer("Пользователь не найден.", reply_markup=admin_panel_keyboard())
        return

    text = f"Подписка продлена: {user.get('full_name')} до {user.get('tariff_until')}"
    if edit:
        try:
            await message.edit_text(f"✅ {text}\n\n{application_card(user)}")
        except Exception:
            await message.answer(text, reply_markup=admin_panel_keyboard())
    else:
        await message.answer(text, reply_markup=admin_panel_keyboard())

    try:
        await message.bot.send_message(
            user_id,
            f"Подписка продлена до <b>{user.get('tariff_until')}</b>.",
            reply_markup=main_menu_keyboard(),
        )
    except Exception:
        pass
