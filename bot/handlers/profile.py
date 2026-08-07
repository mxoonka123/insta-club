from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import DB_PATH
from bot.database import save_profile
from bot.keyboards import (
    BTN_CHANGE_NAME,
    BTN_CREATE_PROFILE,
    BTN_KEEP_NAME,
    BTN_SKIP,
    main_menu_keyboard,
    name_choice_keyboard,
    remove_keyboard,
    skip_keyboard,
    spheres_keyboard,
)
from bot.states import ProfileForm

router = Router(name="profile")


def format_summary(data: dict) -> str:
    instagram = data.get("instagram") or "не указан"
    hobby = data.get("hobby") or "не указано"
    return (
        "📋 <b>Твоя анкета</b>\n"
        f"👤 Имя: {data.get('full_name')}\n"
        f"🏷 Сфера: {data.get('sphere')}\n"
        f"💼 Чем занимаешься: {data.get('activity')}\n"
        f"📸 Instagram: {instagram}\n"
        f"🎯 Хобби: {hobby}"
    )


async def ask_photo(message: Message, state: FSMContext) -> None:
    await state.set_state(ProfileForm.waiting_photo)
    await message.answer(
        "Отлично! Теперь пришли своё фото 📷",
        reply_markup=remove_keyboard(),
    )


@router.message(F.text == BTN_CREATE_PROFILE)
async def start_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProfileForm.waiting_name_choice)

    telegram_name = message.from_user.full_name if message.from_user else "Без имени"
    await state.update_data(telegram_full_name=telegram_name)

    await message.answer(
        f"Как тебя представить?\n\n"
        f"Сейчас в Telegram: <b>{telegram_name}</b>\n\n"
        "Можешь оставить это имя или указать другое.",
        reply_markup=name_choice_keyboard(),
    )


@router.message(ProfileForm.waiting_name_choice, F.text == BTN_KEEP_NAME)
async def keep_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(full_name=data["telegram_full_name"])
    await ask_photo(message, state)


@router.message(ProfileForm.waiting_name_choice, F.text == BTN_CHANGE_NAME)
async def change_name(message: Message, state: FSMContext) -> None:
    await state.set_state(ProfileForm.waiting_name_input)
    await message.answer(
        "Напиши Имя и Фамилию одним сообщением:",
        reply_markup=remove_keyboard(),
    )


@router.message(ProfileForm.waiting_name_choice)
async def invalid_name_choice(message: Message) -> None:
    await message.answer(
        "Выбери один из вариантов на клавиатуре ниже.",
        reply_markup=name_choice_keyboard(),
    )


@router.message(ProfileForm.waiting_name_input, F.text)
async def process_custom_name(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Напиши Имя и Фамилию ещё раз.")
        return

    await state.update_data(full_name=full_name)
    await ask_photo(message, state)


@router.message(ProfileForm.waiting_name_input)
async def invalid_custom_name(message: Message) -> None:
    await message.answer("Нужен текстовый ответ. Напиши Имя и Фамилию.")


@router.message(ProfileForm.waiting_photo, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await state.set_state(ProfileForm.waiting_sphere)
    await message.answer(
        "Выбери сферу деятельности:",
        reply_markup=spheres_keyboard(),
    )


@router.message(ProfileForm.waiting_photo)
async def invalid_photo(message: Message) -> None:
    await message.answer("Пожалуйста, отправь именно фотографию (не файл и не текст).")


@router.callback_query(ProfileForm.waiting_sphere, F.data.startswith("sphere:"))
async def process_sphere(callback: CallbackQuery, state: FSMContext) -> None:
    sphere = (callback.data or "").removeprefix("sphere:")
    await state.update_data(sphere=sphere)
    await state.set_state(ProfileForm.waiting_activity)

    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"Сфера: <b>{sphere}</b>\n\nЧем именно занимаешься?"
        )
    await callback.answer()


@router.callback_query(ProfileForm.waiting_sphere)
async def invalid_sphere_callback(callback: CallbackQuery) -> None:
    await callback.answer("Сначала выбери сферу из списка.", show_alert=True)


@router.message(ProfileForm.waiting_sphere)
async def invalid_sphere_message(message: Message) -> None:
    await message.answer(
        "Выбери сферу кнопкой под сообщением выше.",
        reply_markup=spheres_keyboard(),
    )


@router.message(ProfileForm.waiting_activity, F.text)
async def process_activity(message: Message, state: FSMContext) -> None:
    activity = (message.text or "").strip()
    if len(activity) < 3:
        await message.answer("Опиши чуть подробнее, чем ты занимаешься.")
        return

    await state.update_data(activity=activity)
    await state.set_state(ProfileForm.waiting_instagram)
    await message.answer(
        "Укажи ник Instagram (необязательно):",
        reply_markup=skip_keyboard(),
    )


@router.message(ProfileForm.waiting_activity)
async def invalid_activity(message: Message) -> None:
    await message.answer("Нужен текстовый ответ. Чем именно занимаешься?")


@router.message(ProfileForm.waiting_instagram, F.text == BTN_SKIP)
async def skip_instagram(message: Message, state: FSMContext) -> None:
    await state.update_data(instagram=None)
    await state.set_state(ProfileForm.waiting_hobby)
    await message.answer(
        "Расскажи про отдых и хобби (необязательно):",
        reply_markup=skip_keyboard(),
    )


@router.message(ProfileForm.waiting_instagram, F.text)
async def process_instagram(message: Message, state: FSMContext) -> None:
    instagram = (message.text or "").strip()
    await state.update_data(instagram=instagram)
    await state.set_state(ProfileForm.waiting_hobby)
    await message.answer(
        "Расскажи про отдых и хобби (необязательно):",
        reply_markup=skip_keyboard(),
    )


@router.message(ProfileForm.waiting_instagram)
async def invalid_instagram(message: Message) -> None:
    await message.answer(
        "Отправь ник текстом или нажми «Пропустить ⏭».",
        reply_markup=skip_keyboard(),
    )


@router.message(ProfileForm.waiting_hobby, F.text == BTN_SKIP)
async def skip_hobby(message: Message, state: FSMContext) -> None:
    await state.update_data(hobby=None)
    await finish_profile(message, state)


@router.message(ProfileForm.waiting_hobby, F.text)
async def process_hobby(message: Message, state: FSMContext) -> None:
    hobby = (message.text or "").strip()
    await state.update_data(hobby=hobby)
    await finish_profile(message, state)


@router.message(ProfileForm.waiting_hobby)
async def invalid_hobby(message: Message) -> None:
    await message.answer(
        "Отправь текст о хобби или нажми «Пропустить ⏭».",
        reply_markup=skip_keyboard(),
    )


async def finish_profile(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    telegram_id = message.from_user.id if message.from_user else 0

    save_profile(
        DB_PATH,
        telegram_id=telegram_id,
        full_name=data["full_name"],
        photo_file_id=data["photo_file_id"],
        sphere=data["sphere"],
        activity=data["activity"],
        instagram=data.get("instagram"),
        hobby=data.get("hobby"),
    )

    await state.clear()
    await message.answer(
        "Профиль успешно создан!",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer_photo(
        photo=data["photo_file_id"],
        caption=format_summary(data),
    )
