from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import CURATOR_USERNAME, DB_PATH
from bot.database import list_payments
from bot.helpers import format_date, require_member
from bot.keyboards import BTN_SUBSCRIPTION, main_menu_keyboard, subscription_keyboard

router = Router(name="subscription")


@router.message(StateFilter(None), F.text == BTN_SUBSCRIPTION)
async def subscription_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await require_member(message)
    if not user:
        return

    text = (
        "💳 <b>Подписка</b>\n\n"
        f"Ваш тариф: <b>{user.get('tariff') or '—'}</b>\n"
        f"Оплачен до: <b>{format_date(user.get('tariff_until'))}</b>\n\n"
        "Оплату онлайн подключим позже. Сейчас доступ демо-тарифа Business."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())
    await message.answer("Управление:", reply_markup=subscription_keyboard())


@router.callback_query(F.data == "sub:renew")
async def sub_renew(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Продление пока вручную через куратора.\n"
            f"Напишите: @{CURATOR_USERNAME}"
        )


@router.callback_query(F.data == "sub:change")
async def sub_change(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Доступные тарифы: Start / Business / Pro.\n"
            f"Чтобы сменить тариф, напишите куратору @{CURATOR_USERNAME}."
        )


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
            f"• {item.get('created_at')}: {item.get('amount') or '—'} — {item.get('description') or ''}"
        )
    await callback.message.answer("\n".join(lines))
