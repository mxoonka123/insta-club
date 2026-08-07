from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# Welcome
BTN_JOIN = "Стать участником"
BTN_ABOUT = "Что внутри клуба"
BTN_TARIFFS = "Тарифы"
BTN_REVIEWS = "Отзывы"
BTN_CURATOR = "Связаться с куратором"

# Main menu
BTN_HOME = "🏠 Главная"
BTN_COMMUNITY = "👥 Сообщество"
BTN_KNOWLEDGE = "📚 База знаний"
BTN_EVENTS = "🎟 Мероприятия"
BTN_SUBSCRIPTION = "💳 Подписка"
BTN_REFERRAL = "🎁 Пригласить друга"
BTN_PROFILE = "⚙ Профиль"

# Community
BTN_INTRODUCE = "Представиться"
BTN_FIND_PARTNERS = "Найти партнеров"
BTN_CATALOG = "Каталог участников"
BTN_NEW_MEMBERS = "Новые участники недели"
BTN_SEARCH_NICHES = "Поиск по нишам"
BTN_BACK_MENU = "← В меню"

CITIES = ["Белград", "Нови-Сад", "Ниш", "Другое"]
ONBOARDING_NICHES = [
    "Красота",
    "Недвижимость",
    "Туризм",
    "Маркетинг",
    "Образование",
    "Другое",
]
GOALS = [
    "Новые знакомства",
    "Партнеров",
    "Клиентов",
    "Развитие личного бренда",
    "Контент",
]
CATALOG_NICHES = [
    "Маркетологи",
    "Салоны красоты",
    "Рестораны",
    "Фотографы",
    "Юристы",
    "Косметологи",
    "Риелторы",
    "IT",
    "Другое",
]

# Map onboarding niche labels to catalog niches where possible
NICHE_TO_CATALOG = {
    "Красота": "Салоны красоты",
    "Недвижимость": "Риелторы",
    "Туризм": "Другое",
    "Маркетинг": "Маркетологи",
    "Образование": "Другое",
    "Другое": "Другое",
}


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def welcome_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_JOIN)],
            [KeyboardButton(text=BTN_ABOUT)],
            [KeyboardButton(text=BTN_TARIFFS), KeyboardButton(text=BTN_REVIEWS)],
            [KeyboardButton(text=BTN_CURATOR)],
        ],
        resize_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_HOME)],
            [KeyboardButton(text=BTN_COMMUNITY), KeyboardButton(text=BTN_KNOWLEDGE)],
            [KeyboardButton(text=BTN_EVENTS), KeyboardButton(text=BTN_SUBSCRIPTION)],
            [KeyboardButton(text=BTN_REFERRAL), KeyboardButton(text=BTN_PROFILE)],
        ],
        resize_keyboard=True,
    )


def community_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_INTRODUCE)],
            [KeyboardButton(text=BTN_FIND_PARTNERS)],
            [KeyboardButton(text=BTN_CATALOG)],
            [KeyboardButton(text=BTN_NEW_MEMBERS)],
            [KeyboardButton(text=BTN_SEARCH_NICHES)],
            [KeyboardButton(text=BTN_BACK_MENU)],
        ],
        resize_keyboard=True,
    )


def back_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK_MENU)]],
        resize_keyboard=True,
    )


def choices_keyboard(options: list[str], row_width: int = 2) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for option in options:
        row.append(KeyboardButton(text=option))
        if len(row) >= row_width:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def catalog_keyboard() -> ReplyKeyboardMarkup:
    return choices_keyboard(CATALOG_NICHES + [BTN_BACK_MENU], row_width=2)


def knowledge_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        ("Новые статьи", "kb:new"),
        ("Контент", "kb:content"),
        ("Instagram", "kb:instagram"),
        ("Reels", "kb:reels"),
        ("Личный бренд", "kb:brand"),
        ("Продажи", "kb:sales"),
        ("Нетворкинг", "kb:networking"),
        ("Сербия", "kb:serbia"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=data)]
            for title, data in buttons
        ]
    )


def events_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        ("Завтрак предпринимателей", "event:breakfast"),
        ("Контент-день", "event:content_day"),
        ("Мастермайнд", "event:mastermind"),
        ("Воркшоп", "event:workshop"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=data)]
            for title, data in buttons
        ]
    )


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продлить", callback_data="sub:renew")],
            [InlineKeyboardButton(text="Изменить тариф", callback_data="sub:change")],
            [InlineKeyboardButton(text="История платежей", callback_data="sub:history")],
        ]
    )


def member_card_keyboard(instagram: str | None, username: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if instagram:
        url = instagram if instagram.startswith("http") else f"https://instagram.com/{instagram.lstrip('@')}"
        rows.append([InlineKeyboardButton(text="Instagram", url=url)])
    if username:
        rows.append(
            [InlineKeyboardButton(text="Написать", url=f"https://t.me/{username}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_settings_keyboard(notifications_enabled: bool) -> InlineKeyboardMarkup:
    label = "Выключить уведомления" if notifications_enabled else "Включить уведомления"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data="profile:toggle_notify")],
            [InlineKeyboardButton(text="Правила клуба", callback_data="profile:rules")],
        ]
    )


def after_onboarding_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Правила клуба", callback_data="profile:rules")],
            [InlineKeyboardButton(text="Открыть сообщество", callback_data="go:community")],
        ]
    )
