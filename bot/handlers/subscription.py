from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from bot.config import CURATOR_USERNAME, DB_PATH
from bot.database import list_payments
from bot.helpers import format_date, require_member
from bot.keyboards import BTN_SUBSCRIPTION, main_menu_keyboard, subscription_keyboard
from bot.notify import notify_admins
from bot import texts

router = Router(name="subscription")


@router.message(StateFilter(None), F.text == BTN_SUBSCRIPTION)
async def subscription_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await require_member(message)
    if not user:
        return

    text = (
        "💳 <b>Подписка</b>\n\n"
        f"Ваш тариф: <b>{user.get('tariff') or 'Business'}</b>\n"
        f"Оплачен до: <b>{format_date(user.get('tariff_until'))}</b>\n\n"
        "Продление: оплатите тариф и нажмите «Продлить» — куратор подтвердит."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())
    await message.answer("Управление:", reply_markup=subscription_keyboard())


@router.callback_query(F.data == "sub:renew")
async def sub_renew(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.from_user or not callback.message:
        return

    await callback.message.answer(
        "Заявка на продление отправлена куратору.\n"
        f"Также можете написать напрямую: @{CURATOR_USERNAME}"
    )
    await notify_admins(
        callback.bot,
        "🔁 Запрос на продление подписки\n"
        f"ID: <code>{callback.from_user.id}</code>\n"
        f"Username: @{callback.from_user.username or '—'}\n"
        f"Команда: /renew {callback.from_user.id}",
    )


@router.callback_query(F.data == "sub:tariffs")
async def sub_tariffs(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(texts.TARIFFS)


@router.callback_query(F.data == "sub:history")
async def sub_history(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.from_user or not callback.message:
        return
    payments = list_payments(DB_PATH, callback.from_user.id)
    if not payments:
        await callback.message.answer("История платежей пока пуста.")
        return
    lines = ["<b>История платежей</b>"]
    for item in payments:
        lines.append(
            f"• {format_date(item.get('created_at'))}: "
            f"{item.get('amount') or '—'} — {item.get('description') or ''}"
        )
    await callback.message.answer("\n".join(lines))
