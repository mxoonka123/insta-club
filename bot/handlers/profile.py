from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import DB_PATH
from bot.database import get_user, set_notifications
from bot.helpers import profile_text, require_member
from bot.keyboards import BTN_PROFILE, main_menu_keyboard, profile_settings_keyboard
from bot import texts

router = Router(name="profile")


@router.message(StateFilter(None), F.text == BTN_PROFILE)
async def profile_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await require_member(message)
    if not user:
        return

    await message.answer(
        profile_text(user),
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(
        "Настройки уведомлений:",
        reply_markup=profile_settings_keyboard(bool(user.get("notifications_enabled"))),
    )


@router.callback_query(F.data == "profile:toggle_notify")
async def toggle_notifications(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    user = get_user(DB_PATH, callback.from_user.id)
    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    enabled = not bool(user.get("notifications_enabled"))
    set_notifications(DB_PATH, callback.from_user.id, enabled)
    user = get_user(DB_PATH, callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=profile_settings_keyboard(bool(user and user.get("notifications_enabled")))
    )
    await callback.answer("Уведомления включены" if enabled else "Уведомления выключены")


@router.callback_query(F.data == "profile:rules")
async def show_rules(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(texts.RULES)
