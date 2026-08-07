from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.helpers import require_member
from bot.keyboards import BTN_KNOWLEDGE, knowledge_keyboard, main_menu_keyboard
from bot import texts

router = Router(name="knowledge")


@router.message(StateFilter(None), F.text == BTN_KNOWLEDGE)
async def knowledge_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await message.answer(
        texts.KNOWLEDGE_INTRO,
        reply_markup=main_menu_keyboard(),
    )
    await message.answer("Темы:", reply_markup=knowledge_keyboard())


@router.callback_query(F.data.startswith("kb:"))
async def knowledge_topic(callback: CallbackQuery) -> None:
    key = (callback.data or "").removeprefix("kb:")
    content = texts.KNOWLEDGE_TOPICS.get(key)
    if not content:
        await callback.answer("Тема не найдена", show_alert=True)
        return
    if callback.message:
        await callback.message.answer(content)
    await callback.answer()
