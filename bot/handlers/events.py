from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.helpers import require_member
from bot.keyboards import BTN_EVENTS, events_keyboard, main_menu_keyboard
from bot import texts

router = Router(name="events")


@router.message(StateFilter(None), F.text == BTN_EVENTS)
async def events_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await message.answer(texts.EVENTS_INTRO, reply_markup=main_menu_keyboard())
    await message.answer("Выберите мероприятие:", reply_markup=events_keyboard())


@router.callback_query(F.data.startswith("event:"))
async def event_details(callback: CallbackQuery) -> None:
    key = (callback.data or "").removeprefix("event:")
    content = texts.EVENTS.get(key)
    if not content:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    if callback.message:
        await callback.message.answer(
            content + "\n\nЗапись на события подключим в следующем обновлении."
        )
    await callback.answer()
