from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, User

from bot.config import DB_PATH
from bot.database import STATUS_ACTIVE, STATUS_PENDING, STATUS_REJECTED, get_user, mark_payment_claimed
from bot.helpers import application_card, status_label
from bot.keyboards import (
    BTN_I_PAID,
    BTN_MY_STATUS,
    application_admin_keyboard,
    pending_keyboard,
    welcome_keyboard,
)
from bot.notify import notify_admins
from bot import texts

router = Router(name="payment")


async def claim_payment(bot: Bot, user: User, answer) -> None:
    db_user = get_user(DB_PATH, user.id)
    if not db_user:
        await answer(
            "Сначала подайте заявку — нажмите «Стать участником».",
            reply_markup=welcome_keyboard(),
        )
        return

    if db_user.get("status") == STATUS_ACTIVE:
        await answer("У вас уже открыт доступ в клуб.")
        return

    if db_user.get("status") not in {STATUS_PENDING, STATUS_REJECTED}:
        await answer(
            "Сначала завершите анкету — нажмите «Стать участником».",
            reply_markup=welcome_keyboard(),
        )
        return

    updated = mark_payment_claimed(DB_PATH, user.id)
    await answer(texts.PAYMENT_CLAIMED, reply_markup=pending_keyboard())

    if updated:
        await notify_admins(
            bot,
            "💳 Пользователь отметил оплату\n\n" + application_card(updated),
            reply_markup=application_admin_keyboard(int(updated["telegram_id"])),
        )


@router.message(StateFilter(None), F.text == BTN_I_PAID)
async def paid_button(message: Message) -> None:
    if not message.from_user:
        return
    await claim_payment(message.bot, message.from_user, message.answer)


@router.callback_query(F.data == "pay:claimed")
async def paid_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.from_user or not callback.message:
        return
    await claim_payment(callback.bot, callback.from_user, callback.message.answer)


@router.message(StateFilter(None), F.text == BTN_MY_STATUS)
async def my_status(message: Message) -> None:
    if not message.from_user:
        return
    user = get_user(DB_PATH, message.from_user.id)
    if not user:
        await message.answer("Заявка ещё не создана.", reply_markup=welcome_keyboard())
        return

    text = (
        f"Статус: <b>{status_label(user)}</b>\n"
        f"Тариф: {user.get('tariff') or 'Business'}\n"
    )
    if user.get("status") == STATUS_PENDING:
        text += "\n" + texts.PENDING_ACCESS
        await message.answer(text, reply_markup=pending_keyboard())
        return

    await message.answer(text)
