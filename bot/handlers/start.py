from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import CURATOR_USERNAME, DB_PATH
from bot.database import ensure_user, get_user, get_user_by_referral_code
from bot.keyboards import (
    BTN_ABOUT,
    BTN_CURATOR,
    BTN_HOME,
    BTN_JOIN,
    BTN_REVIEWS,
    BTN_TARIFFS,
    main_menu_keyboard,
    remove_keyboard,
    welcome_keyboard,
)
from bot.states import Onboarding
from bot import texts

router = Router(name="start")


def _parse_referral(command: CommandObject | None) -> int | None:
    if not command or not command.args:
        return None
    code = command.args.strip()
    referrer = get_user_by_referral_code(DB_PATH, code)
    if referrer:
        return int(referrer["telegram_id"])
    return None


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    command: CommandObject,
) -> None:
    await state.clear()
    if not message.from_user:
        return

    referred_by = _parse_referral(command)
    if referred_by == message.from_user.id:
        referred_by = None

    user = ensure_user(
        DB_PATH,
        message.from_user.id,
        message.from_user.username,
        referred_by=referred_by,
    )

    if user.get("is_member"):
        await message.answer(texts.WELCOME, reply_markup=main_menu_keyboard())
        return

    await message.answer(texts.WELCOME, reply_markup=welcome_keyboard())


@router.message(F.text == BTN_HOME)
async def home(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user:
        return
    user = get_user(DB_PATH, message.from_user.id)
    if user and user.get("is_member"):
        await message.answer(
            texts.WELCOME + "\n\nВы в главном меню клуба.",
            reply_markup=main_menu_keyboard(),
        )
        return
    await message.answer(texts.WELCOME, reply_markup=welcome_keyboard())


@router.message(F.text == BTN_ABOUT)
async def about(message: Message) -> None:
    await message.answer(texts.ABOUT_CLUB)


@router.message(F.text == BTN_TARIFFS)
async def tariffs(message: Message) -> None:
    await message.answer(texts.TARIFFS)


@router.message(F.text == BTN_REVIEWS)
async def reviews(message: Message) -> None:
    await message.answer(texts.REVIEWS)


@router.message(F.text == BTN_CURATOR)
async def curator(message: Message) -> None:
    await message.answer(
        f"Связаться с куратором: @{CURATOR_USERNAME}\n"
        f"https://t.me/{CURATOR_USERNAME}"
    )


@router.message(F.text == BTN_JOIN)
async def join_club(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return

    user = ensure_user(
        DB_PATH,
        message.from_user.id,
        message.from_user.username,
    )
    if user.get("is_member"):
        await message.answer(
            "Вы уже участник клуба. Открываю главное меню.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(Onboarding.name)
    await message.answer(texts.ONBOARDING_INTRO, reply_markup=remove_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await home(message, state)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user:
        return
    user = get_user(DB_PATH, message.from_user.id)
    if user and user.get("is_member"):
        await message.answer("Отменено.", reply_markup=main_menu_keyboard())
        return
    await message.answer("Отменено.", reply_markup=welcome_keyboard())
