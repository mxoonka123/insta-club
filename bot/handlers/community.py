from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import DB_PATH
from bot.database import list_by_niche, list_new_members, search_members, update_intro
from bot.helpers import require_member, send_member_cards
from bot.keyboards import (
    BTN_BACK_MENU,
    BTN_CATALOG,
    BTN_COMMUNITY,
    BTN_FIND_PARTNERS,
    BTN_INTRODUCE,
    BTN_NEW_MEMBERS,
    BTN_SEARCH_NICHES,
    CATALOG_NICHES,
    catalog_keyboard,
    community_keyboard,
    main_menu_keyboard,
    remove_keyboard,
)
from bot.states import Introduce, SearchPartners
from bot import texts

router = Router(name="community")


async def open_community(message: Message) -> None:
    await message.answer(texts.COMMUNITY_INTRO, reply_markup=community_keyboard())


@router.message(StateFilter(None), F.text == BTN_COMMUNITY)
async def community_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await open_community(message)


@router.callback_query(F.data == "go:community")
async def community_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message and callback.from_user:
        from bot.database import get_user

        user = get_user(DB_PATH, callback.from_user.id)
        if not user or not user.get("is_member"):
            await callback.answer("Сначала завершите онбординг", show_alert=True)
            return
        await open_community(callback.message)
    await callback.answer()


@router.message(StateFilter(None), F.text == BTN_BACK_MENU)
async def back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await message.answer("Главное меню", reply_markup=main_menu_keyboard())


@router.message(StateFilter(None), F.text == BTN_INTRODUCE)
async def introduce_start(message: Message, state: FSMContext) -> None:
    if not await require_member(message):
        return
    await state.set_state(Introduce.text)
    await message.answer(
        "Напишите короткое представление:\n"
        "кто вы, чем занимаетесь и какой сейчас запрос.",
        reply_markup=remove_keyboard(),
    )


@router.message(Introduce.text, F.text)
async def introduce_save(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    text = (message.text or "").strip()
    if len(text) < 10:
        await message.answer("Добавьте чуть больше деталей — минимум пару предложений.")
        return
    update_intro(DB_PATH, message.from_user.id, text)
    await state.clear()
    await message.answer(
        "Представление сохранено. Его увидят в вашей карточке и в новых участниках.",
        reply_markup=community_keyboard(),
    )


@router.message(Introduce.text)
async def introduce_invalid(message: Message) -> None:
    await message.answer("Отправьте представление текстом.")


@router.message(StateFilter(None), F.text == BTN_FIND_PARTNERS)
async def find_partners_start(message: Message, state: FSMContext) -> None:
    if not await require_member(message):
        return
    await state.set_state(SearchPartners.query)
    await message.answer(
        "Опишите, кого ищете: ниша, город или запрос.\n"
        "Например: «маркетолог Белград» или «фотограф».",
        reply_markup=remove_keyboard(),
    )


@router.message(SearchPartners.query, F.text)
async def find_partners_search(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    await state.clear()
    members = search_members(DB_PATH, query)
    await send_member_cards(
        message,
        members,
        "Пока никого не нашли. Попробуйте другой запрос или откройте каталог.",
    )
    await message.answer("Сообщество", reply_markup=community_keyboard())


@router.message(SearchPartners.query)
async def find_partners_invalid(message: Message) -> None:
    await message.answer("Отправьте поисковый запрос текстом.")


@router.message(StateFilter(None), F.text == BTN_CATALOG)
async def catalog_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await message.answer(
        "Каталог участников\n\nВыберите нишу:",
        reply_markup=catalog_keyboard(),
    )


@router.message(StateFilter(None), F.text.in_(CATALOG_NICHES))
async def catalog_niche(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    niche = message.text or ""
    members = list_by_niche(DB_PATH, niche)
    await message.answer(f"<b>{niche}</b>")
    await send_member_cards(
        message,
        members,
        f"В нише «{niche}» пока нет участников.",
    )
    await message.answer("Выберите другую нишу или вернитесь в меню.", reply_markup=catalog_keyboard())


@router.message(StateFilter(None), F.text == BTN_NEW_MEMBERS)
async def new_members(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    members = list_new_members(DB_PATH, limit=8)
    await message.answer("<b>Новые участники недели</b>")
    await send_member_cards(message, members, "Пока нет новых участников.")
    await message.answer("Сообщество", reply_markup=community_keyboard())


@router.message(StateFilter(None), F.text == BTN_SEARCH_NICHES)
async def search_niches(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await message.answer(
        "Поиск по нишам — выберите категорию:",
        reply_markup=catalog_keyboard(),
    )
