from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import DB_PATH
from bot.database import complete_onboarding, ensure_user, get_user
from bot.helpers import application_card
from bot.keyboards import (
    CITIES,
    GOALS,
    NICHE_TO_CATALOG,
    ONBOARDING_NICHES,
    after_onboarding_keyboard,
    application_admin_keyboard,
    choices_keyboard,
    pending_keyboard,
    remove_keyboard,
)
from bot.notify import notify_admins
from bot.states import Onboarding
from bot import texts

router = Router(name="onboarding")


@router.message(Onboarding.name, F.text)
async def onboarding_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Введите имя ещё раз — минимум 2 символа.")
        return

    await state.update_data(full_name=name)
    await state.set_state(Onboarding.city)
    await message.answer(
        "В каком городе вы работаете?",
        reply_markup=choices_keyboard(CITIES, row_width=2),
    )


@router.message(Onboarding.name)
async def onboarding_name_invalid(message: Message) -> None:
    await message.answer("Нужен текстовый ответ. Как вас зовут?")


@router.message(Onboarding.city, F.text.in_(CITIES))
async def onboarding_city(message: Message, state: FSMContext) -> None:
    city = message.text or ""
    if city == "Другое":
        await state.set_state(Onboarding.city_other)
        await message.answer("Напишите ваш город:", reply_markup=remove_keyboard())
        return

    await state.update_data(city=city)
    await state.set_state(Onboarding.niche)
    await message.answer(
        "Ваша сфера?",
        reply_markup=choices_keyboard(ONBOARDING_NICHES, row_width=2),
    )


@router.message(Onboarding.city)
async def onboarding_city_invalid(message: Message) -> None:
    await message.answer(
        "Выберите город кнопкой ниже.",
        reply_markup=choices_keyboard(CITIES, row_width=2),
    )


@router.message(Onboarding.city_other, F.text)
async def onboarding_city_other(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if len(city) < 2:
        await message.answer("Укажите город текстом.")
        return
    await state.update_data(city=city)
    await state.set_state(Onboarding.niche)
    await message.answer(
        "Ваша сфера?",
        reply_markup=choices_keyboard(ONBOARDING_NICHES, row_width=2),
    )


@router.message(Onboarding.niche, F.text.in_(ONBOARDING_NICHES))
async def onboarding_niche(message: Message, state: FSMContext) -> None:
    niche = message.text or ""
    if niche == "Другое":
        await state.set_state(Onboarding.niche_other)
        await message.answer("Напишите вашу сферу:", reply_markup=remove_keyboard())
        return

    await state.update_data(niche=NICHE_TO_CATALOG.get(niche, niche))
    await state.set_state(Onboarding.instagram)
    await message.answer(
        "Instagram\n\nВведите ссылку или @ник:",
        reply_markup=remove_keyboard(),
    )


@router.message(Onboarding.niche)
async def onboarding_niche_invalid(message: Message) -> None:
    await message.answer(
        "Выберите сферу кнопкой ниже.",
        reply_markup=choices_keyboard(ONBOARDING_NICHES, row_width=2),
    )


@router.message(Onboarding.niche_other, F.text)
async def onboarding_niche_other(message: Message, state: FSMContext) -> None:
    niche = (message.text or "").strip()
    if len(niche) < 2:
        await message.answer("Укажите сферу текстом.")
        return
    await state.update_data(niche=niche)
    await state.set_state(Onboarding.instagram)
    await message.answer("Instagram\n\nВведите ссылку или @ник:")


@router.message(Onboarding.instagram, F.text)
async def onboarding_instagram(message: Message, state: FSMContext) -> None:
    instagram = (message.text or "").strip()
    if len(instagram) < 2:
        await message.answer("Введите ссылку на Instagram или @ник.")
        return

    await state.update_data(instagram=instagram)
    await state.set_state(Onboarding.goal)
    await message.answer(
        "Что хотите получить?",
        reply_markup=choices_keyboard(GOALS, row_width=1),
    )


@router.message(Onboarding.instagram)
async def onboarding_instagram_invalid(message: Message) -> None:
    await message.answer("Нужен текст: ссылка или @ник Instagram.")


@router.message(Onboarding.goal, F.text.in_(GOALS))
async def onboarding_goal(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return

    goal = message.text or ""
    data = await state.get_data()
    ensure_user(DB_PATH, message.from_user.id, message.from_user.username)

    complete_onboarding(
        DB_PATH,
        telegram_id=message.from_user.id,
        full_name=data["full_name"],
        city=data["city"],
        niche=data["niche"],
        instagram=data["instagram"],
        goal=goal,
    )
    await state.clear()

    user = get_user(DB_PATH, message.from_user.id)
    await message.answer(texts.AFTER_REGISTRATION, reply_markup=pending_keyboard())
    await message.answer("Дальше:", reply_markup=after_onboarding_keyboard())

    if user:
        await notify_admins(
            message.bot,
            "🆕 Новая заявка в клуб\n\n" + application_card(user),
            reply_markup=application_admin_keyboard(int(user["telegram_id"])),
        )


@router.message(Onboarding.goal)
async def onboarding_goal_invalid(message: Message) -> None:
    await message.answer(
        "Выберите цель кнопкой ниже.",
        reply_markup=choices_keyboard(GOALS, row_width=1),
    )
