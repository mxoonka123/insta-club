from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import BOT_USERNAME, DB_PATH
from bot.database import count_referrals
from bot.helpers import require_member
from bot.keyboards import BTN_REFERRAL, main_menu_keyboard
from bot import texts

router = Router(name="referral")


@router.message(StateFilter(None), F.text == BTN_REFERRAL)
async def referral_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await require_member(message)
    if not user:
        return

    code = user.get("referral_code") or ""
    invited = count_referrals(DB_PATH, int(user["telegram_id"]))
    username = BOT_USERNAME or "your_bot"
    link = f"https://t.me/{username}?start={code}"

    await message.answer(
        f"{texts.REFERRAL_INTRO}\n\n"
        f"Ваша ссылка:\n{link}\n\n"
        f"Приглашено: <b>{invited}</b> человек",
        reply_markup=main_menu_keyboard(),
    )
