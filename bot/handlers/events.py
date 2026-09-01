from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_IDS, DB_PATH
from bot.database import (
    add_topic_suggestion,
    cancel_rsvp,
    count_rsvps,
    create_meeting,
    get_meeting,
    get_upcoming_meeting,
    has_rsvp,
    list_active_members,
    list_meetings_for_admin,
    list_past_meetings,
    list_rsvp_users,
    rsvp_meeting,
    unpublish_meeting,
)
from bot.helpers import require_member
from bot.keyboards import (
    BTN_EVENTS,
    admin_meetings_keyboard,
    admin_panel_keyboard,
    main_menu_keyboard,
    meeting_city_keyboard,
    meeting_format_keyboard,
    meeting_publish_keyboard,
    meeting_rsvp_keyboard,
    meetings_hub_keyboard,
    remove_keyboard,
)
from bot.meetings import (
    format_admin_meeting_line,
    format_announce,
    format_archive_item,
    format_meeting,
    meeting_is_upcoming,
    parse_local_datetime,
)
from bot.notify import notify_admins
from bot.states import CreateMeeting, SuggestTopic
from bot import texts

router = Router(name="events")


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMIN_IDS)


async def _broadcast_meeting(bot, meeting: dict) -> int:
    sent = 0
    text = format_announce(meeting)
    for member in list_active_members(DB_PATH):
        telegram_id = int(member["telegram_id"])
        try:
            await bot.send_message(
                telegram_id,
                text,
                reply_markup=meeting_rsvp_keyboard(int(meeting["id"]), False),
            )
            sent += 1
        except Exception:
            continue
    return sent


@router.message(StateFilter(None), F.text == BTN_EVENTS)
async def events_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not await require_member(message):
        return
    await message.answer(texts.MEETINGS_INTRO, reply_markup=main_menu_keyboard())
    await message.answer("Выберите действие:", reply_markup=meetings_hub_keyboard())


@router.callback_query(F.data == "meet:next")
async def show_next_meeting(callback: CallbackQuery) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    meeting = get_upcoming_meeting(DB_PATH)
    if not meeting:
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                "Ближайшая встреча ещё не объявлена.\n"
                "Команда INSTA CLUB опубликует дату, формат и тему здесь."
            )
        return

    already = has_rsvp(DB_PATH, int(meeting["id"]), callback.from_user.id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            format_meeting(meeting, DB_PATH),
            reply_markup=meeting_rsvp_keyboard(int(meeting["id"]), already),
        )


@router.callback_query(F.data.startswith("meet:rsvp:"))
async def rsvp_callback(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    meeting_id = int((callback.data or "").split(":")[-1])
    result = rsvp_meeting(DB_PATH, meeting_id, callback.from_user.id)
    if result == "missing":
        await callback.answer("Встреча не найдена", show_alert=True)
        return
    if result == "full":
        await callback.answer("Мест больше нет", show_alert=True)
        return
    await callback.answer("Вы записаны")
    meeting = get_meeting(DB_PATH, meeting_id)
    if meeting:
        await callback.message.edit_text(
            format_meeting(meeting, DB_PATH),
            reply_markup=meeting_rsvp_keyboard(meeting_id, True),
        )


@router.callback_query(F.data.startswith("meet:cancel:"))
async def cancel_rsvp_callback(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    meeting_id = int((callback.data or "").split(":")[-1])
    cancel_rsvp(DB_PATH, meeting_id, callback.from_user.id)
    await callback.answer("Запись отменена")
    meeting = get_meeting(DB_PATH, meeting_id)
    if meeting:
        await callback.message.edit_text(
            format_meeting(meeting, DB_PATH),
            reply_markup=meeting_rsvp_keyboard(meeting_id, False),
        )


@router.callback_query(F.data == "meet:topic")
async def suggest_topic_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(SuggestTopic.text)
    if callback.message:
        await callback.message.answer(
            "Какую тему встречи хотите предложить?\n"
            "Напишите одним сообщением.",
            reply_markup=remove_keyboard(),
        )


@router.message(SuggestTopic.text, F.text, ~F.text.startswith("/"))
async def suggest_topic_save(callback_message: Message, state: FSMContext) -> None:
    if not callback_message.from_user:
        return
    topic = (callback_message.text or "").strip()
    if len(topic) < 4:
        await callback_message.answer("Добавьте чуть больше деталей.")
        return
    add_topic_suggestion(DB_PATH, callback_message.from_user.id, topic)
    await state.clear()
    await callback_message.answer(
        "Спасибо, тему передали команде INSTA CLUB.",
        reply_markup=main_menu_keyboard(),
    )
    username = callback_message.from_user.username
    who = f"@{username}" if username else str(callback_message.from_user.id)
    await notify_admins(
        callback_message.bot,
        f"💡 Тема для встречи от {who}:\n{topic}",
    )


@router.callback_query(F.data == "meet:archive")
async def show_archive(callback: CallbackQuery) -> None:
    await callback.answer()
    past = list_past_meetings(DB_PATH)
    if not callback.message:
        return
    if not past:
        await callback.message.answer("Архив пока пуст — встречи появятся после первой прошедшей.")
        return
    lines = ["<b>Архив встреч</b>\n"]
    for item in past:
        lines.append(format_archive_item(item, DB_PATH))
        lines.append("")
    await callback.message.answer("\n".join(lines).strip())


def _admin_meetings_sections(meetings: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    upcoming: list[dict] = []
    past: list[dict] = []
    unpublished: list[dict] = []
    for item in meetings:
        if not int(item.get("published") or 0):
            unpublished.append(item)
        elif meeting_is_upcoming(item):
            upcoming.append(item)
        else:
            past.append(item)
    upcoming.sort(key=lambda row: str(row.get("starts_at") or ""))
    past.sort(key=lambda row: str(row.get("starts_at") or ""), reverse=True)
    unpublished.sort(key=lambda row: str(row.get("starts_at") or ""), reverse=True)
    return upcoming, past, unpublished


def _admin_meetings_text(meetings: list[dict]) -> str:
    if not meetings:
        return (
            "<b>Встречи клуба</b>\n\n"
            "Пока нет ни одной встречи.\n"
            "Создайте первую: /meeting"
        )

    upcoming, past, unpublished = _admin_meetings_sections(meetings)
    lines = ["<b>Встречи клуба</b>"]

    def _append_group(title: str, items: list[dict]) -> None:
        if not items:
            return
        lines.append("")
        lines.append(f"<b>{title}</b>")
        for item in items:
            lines.append("")
            lines.append(format_admin_meeting_line(item, DB_PATH))

    _append_group("Ближайшие", upcoming)
    _append_group("Прошедшие", past)
    _append_group("Снятые с публикации", unpublished)

    if not upcoming:
        lines.append("")
        lines.append("Ближайшей опубликованной встречи нет.")

    text = "\n".join(lines).strip()
    if len(text) > 3900:
        text = text[:3900].rstrip() + "\n…"
    return text


async def _send_admin_meetings(message: Message) -> None:
    meetings = list_meetings_for_admin(DB_PATH)
    upcoming, past, _unpublished = _admin_meetings_sections(meetings)
    await message.answer(
        _admin_meetings_text(meetings),
        reply_markup=admin_meetings_keyboard(upcoming, past),
    )


def _format_rsvp_list(meeting: dict, people: list[dict]) -> str:
    taken = len(people)
    seats = meeting.get("seats")
    seats_txt = str(taken) if seats is None else f"{taken} / {seats}"
    lines = [
        f"<b>Запись на встречу #{meeting['id']}</b>",
        format_admin_meeting_line(meeting, DB_PATH),
        "",
        f"Всего: {seats_txt}",
    ]
    if not people:
        lines.append("Пока никто не записался.")
        return "\n".join(lines)
    lines.append("")
    for person in people:
        name = person.get("full_name") or "без имени"
        username = person.get("username")
        nick = f" @{username}" if username else ""
        city = person.get("city") or "—"
        telegram_id = person.get("telegram_id")
        lines.append(f"• {name}{nick} · {city} · <code>{telegram_id}</code>")
    text = "\n".join(lines)
    if len(text) > 3900:
        text = text[:3900].rstrip() + "\n…"
    return text


@router.message(Command("meetings"))
async def admin_meetings_command(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    await _send_admin_meetings(message)


@router.callback_query(F.data == "meetadm:list")
async def admin_meetings_button(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await _send_admin_meetings(callback.message)


@router.callback_query(F.data.startswith("meetadm:who:"))
async def admin_meeting_who(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    meeting_id = int((callback.data or "").split(":")[-1])
    meeting = get_meeting(DB_PATH, meeting_id)
    if not meeting:
        await callback.answer("Встреча не найдена", show_alert=True)
        return
    await callback.answer()
    people = list_rsvp_users(DB_PATH, meeting_id)
    if callback.message:
        await callback.message.answer(_format_rsvp_list(meeting, people))


@router.callback_query(F.data.startswith("meetadm:drop:"))
async def admin_meeting_unpublish(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    meeting_id = int((callback.data or "").split(":")[-1])
    meeting = get_meeting(DB_PATH, meeting_id)
    if not meeting:
        await callback.answer("Встреча не найдена", show_alert=True)
        return
    if not int(meeting.get("published") or 0):
        await callback.answer("Уже снята", show_alert=True)
        return
    unpublish_meeting(DB_PATH, meeting_id)
    await callback.answer("Снята с публикации")
    if callback.message:
        await callback.message.answer(
            f"Встреча #{meeting_id} снята с публикации.\n"
            "Участники её больше не видят, напоминания не уйдут.\n"
            "Записи RSVP сохранены."
        )
        await _send_admin_meetings(callback.message)


@router.message(Command("meeting"))
async def create_meeting_command(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    await _start_create_meeting(message, state)


@router.callback_query(F.data == "meetadm:create")
async def create_meeting_button(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await _start_create_meeting(callback.message, state)


async def _start_create_meeting(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Создать встречу\n\nВыберите формат:",
        reply_markup=admin_panel_keyboard(),
    )
    await message.answer("Офлайн или онлайн:", reply_markup=meeting_format_keyboard())


@router.callback_query(F.data == "meetadm:cancel")
async def create_meeting_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.clear()
    await callback.answer("Отменено")
    if callback.message:
        await callback.message.answer(
            "Создание встречи отменено.",
            reply_markup=admin_panel_keyboard(),
        )


@router.callback_query(F.data.startswith("meetadm:fmt:"))
async def create_meeting_format(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    fmt = (callback.data or "").split(":")[-1]
    await state.update_data(format=fmt)
    await callback.answer()
    if not callback.message:
        return
    if fmt == "online":
        await state.update_data(city="Все")
        await state.set_state(CreateMeeting.date)
        await callback.message.answer("Дата встречи в формате 12.09.2026:")
        return
    await callback.message.answer("Город:", reply_markup=meeting_city_keyboard())


@router.callback_query(F.data.startswith("meetadm:city:"))
async def create_meeting_city(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    city = (callback.data or "").split(":")[-1]
    await state.update_data(city=city)
    await state.set_state(CreateMeeting.date)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Дата встречи в формате 12.09.2026:")


@router.message(CreateMeeting.date, F.text, ~F.text.startswith("/"))
async def create_meeting_date(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    parts = raw.replace("/", ".").split(".")
    if len(parts) != 3 or len(parts[2]) != 4:
        await message.answer("Нужна дата с годом из 4 цифр, например 12.09.2026")
        return
    await state.update_data(date=raw)
    await state.set_state(CreateMeeting.time)
    await message.answer("Время в формате 19:00 (по Белграду):")


@router.message(CreateMeeting.time, F.text, ~F.text.startswith("/"))
async def create_meeting_time(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    data = await state.get_data()
    starts = parse_local_datetime(data.get("date", ""), raw)
    if not starts:
        await message.answer("Нужно время вида 19:00")
        return
    await state.update_data(time=raw, starts_at=starts.isoformat(timespec="seconds"))
    await state.set_state(CreateMeeting.topic)
    await message.answer("Тема встречи:")


@router.message(CreateMeeting.topic, F.text, ~F.text.startswith("/"))
async def create_meeting_topic(message: Message, state: FSMContext) -> None:
    topic = (message.text or "").strip()
    if len(topic) < 3:
        await message.answer("Тема слишком короткая.")
        return
    await state.update_data(topic=topic)
    await state.set_state(CreateMeeting.seats)
    await message.answer("Лимит мест — число или «без лимита»:")


@router.message(CreateMeeting.seats, F.text, ~F.text.startswith("/"))
async def create_meeting_seats(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().lower()
    seats = None
    if raw not in {"без лимита", "нет", "0", "-"}:
        if not raw.isdigit() or int(raw) < 1:
            await message.answer("Введите число или «без лимита».")
            return
        seats = int(raw)
    await state.update_data(seats=seats)
    await state.set_state(CreateMeeting.confirm)
    data = await state.get_data()
    preview = {
        "id": 0,
        "format": data.get("format"),
        "city": data.get("city"),
        "starts_at": data.get("starts_at"),
        "topic": data.get("topic"),
        "seats": seats,
    }
    try:
        body = format_meeting(preview, DB_PATH).replace(
            "<b>СЛЕДУЮЩАЯ ВСТРЕЧА ✦</b>",
            "<b>Черновик встречи</b>",
        )
    except Exception:
        body = (
            "<b>Черновик встречи</b>\n\n"
            f"{preview.get('city')} · {preview.get('format')}\n"
            f"Тема: {preview.get('topic')}\n"
            f"Когда: {data.get('date')} {data.get('time')}\n"
            f"Мест: {seats if seats is not None else 'без лимита'}"
        )
    await message.answer(
        "Проверьте встречу:\n\n" + body,
        reply_markup=meeting_publish_keyboard(),
    )


@router.callback_query(CreateMeeting.confirm, F.data == "meetadm:publish")
async def create_meeting_publish(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Нет доступа", show_alert=True)
        return
    data = await state.get_data()
    required = {"format", "city", "starts_at", "topic"}
    if not required.issubset(data):
        await callback.answer("Данные встречи неполные", show_alert=True)
        await state.clear()
        return

    meeting = create_meeting(
        DB_PATH,
        format=data["format"],
        city=data["city"],
        starts_at=data["starts_at"],
        topic=data["topic"],
        seats=data.get("seats"),
    )
    await state.clear()
    await callback.answer("Опубликовано")
    sent = await _broadcast_meeting(callback.bot, meeting)
    if callback.message:
        await callback.message.answer(
            f"Встреча опубликована. Рассылка: {sent} участникам.\n"
            f"Записались: {count_rsvps(DB_PATH, int(meeting['id']))}",
            reply_markup=admin_panel_keyboard(),
        )
