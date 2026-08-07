from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BTN_CREATE_PROFILE = "Создать 👨‍💻 Профиль"
BTN_KEEP_NAME = "Оставляем 👍"
BTN_CHANGE_NAME = "Хочу поменять 🤨"
BTN_SKIP = "Пропустить ⏭"

SPHERES = [
    "📊 Маркетинг",
    "💻 IT & StartUp",
    "🎨 Дизайн",
    "💰 Финансы",
    "🍔 HoReCa",
    "🏗 Недвижимость",
    "🎓 Образование",
    "📝 Другое",
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CREATE_PROFILE)]],
        resize_keyboard=True,
    )


def name_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_KEEP_NAME)],
            [KeyboardButton(text=BTN_CHANGE_NAME)],
        ],
        resize_keyboard=True,
    )


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_SKIP)]],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def spheres_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=sphere, callback_data=f"sphere:{sphere}")]
        for sphere in SPHERES
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
