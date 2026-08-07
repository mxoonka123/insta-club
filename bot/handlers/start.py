from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards import main_menu_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! 👋\n\n"
        "Я помогу собрать твой профиль за несколько коротких шагов.\n"
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=main_menu_keyboard(),
    )
