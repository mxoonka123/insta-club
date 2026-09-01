from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.config import CURATOR_USERNAME

# Welcome
BTN_JOIN = "Стать участником"
BTN_ABOUT = "Что внутри клуба"
BTN_TARIFFS = "Тарифы"
BTN_PARTNERS = "Партнёры"
BTN_CURATOR = "Связаться с куратором"
BTN_I_PAID = "Я оплатил"
BTN_MY_STATUS = "Статус заявки"

# Main menu
BTN_HOME = "🏠 Главная"
BTN_COMMUNITY = "👥 Сообщество"
BTN_KNOWLEDGE = "📚 База знаний"
BTN_EVENTS = "📅 Встречи клуба"
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


def partners_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Mishin Club",
                    url="https://t.me/mishin_club_bot",
                )
            ]
        ]
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def welcome_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_JOIN)],
            [KeyboardButton(text=BTN_ABOUT)],
            [KeyboardButton(text=BTN_TARIFFS), KeyboardButton(text=BTN_PARTNERS)],
            [KeyboardButton(text=BTN_CURATOR)],
        ],
        resize_keyboard=True,
    )


def pending_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_I_PAID)],
            [KeyboardButton(text=BTN_MY_STATUS)],
            [KeyboardButton(text=BTN_TARIFFS), KeyboardButton(text=BTN_CURATOR)],
            [KeyboardButton(text=BTN_ABOUT)],
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


def meetings_hub_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ближайшая встреча", callback_data="meet:next")],
            [InlineKeyboardButton(text="Предложить тему", callback_data="meet:topic")],
            [InlineKeyboardButton(text="Архив встреч", callback_data="meet:archive")],
        ]
    )


def meeting_rsvp_keyboard(meeting_id: int, already: bool) -> InlineKeyboardMarkup:
    if already:
        label = "Вы записаны ✓  ·  отменить"
        data = f"meet:cancel:{meeting_id}"
    else:
        label = "Я участвую"
        data = f"meet:rsvp:{meeting_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=data)]]
    )


def meeting_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Офлайн", callback_data="meetadm:fmt:offline")],
            [InlineKeyboardButton(text="Онлайн", callback_data="meetadm:fmt:online")],
            [InlineKeyboardButton(text="Отмена", callback_data="meetadm:cancel")],
        ]
    )


def meeting_city_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Белград", callback_data="meetadm:city:Белград")],
            [InlineKeyboardButton(text="Нови-Сад", callback_data="meetadm:city:Нови-Сад")],
            [InlineKeyboardButton(text="Отмена", callback_data="meetadm:cancel")],
        ]
    )


def meeting_publish_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Опубликовать", callback_data="meetadm:publish")],
            [InlineKeyboardButton(text="Отмена", callback_data="meetadm:cancel")],
        ]
    )


def admin_extra_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать встречу", callback_data="meetadm:create")],
        ]
    )


def events_keyboard() -> InlineKeyboardMarkup:
    return meetings_hub_keyboard()


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продлить", callback_data="sub:renew")],
            [InlineKeyboardButton(text="Тарифы", callback_data="sub:tariffs")],
            [InlineKeyboardButton(text="История платежей", callback_data="sub:history")],
        ]
    )


def application_admin_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Одобрить",
                    callback_data=f"admin:approve:{telegram_id}",
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"admin:reject:{telegram_id}",
                ),
            ]
        ]
    )


def member_admin_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Закрыть доступ",
                    callback_data=f"admin:kick:{telegram_id}",
                )
            ]
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
            [InlineKeyboardButton(text="Я оплатил", callback_data="pay:claimed")],
            [InlineKeyboardButton(text="Правила клуба", callback_data="profile:rules")],
            [
                InlineKeyboardButton(
                    text="Написать куратору",
                    url=f"https://t.me/{CURATOR_USERNAME}",
                )
            ],
        ]
    )


def after_approval_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Правила клуба", callback_data="profile:rules")],
            [InlineKeyboardButton(text="Открыть сообщество", callback_data="go:community")],
        ]
    )
