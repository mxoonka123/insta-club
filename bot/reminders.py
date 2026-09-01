import asyncio
import logging

from aiogram import Bot

from bot.config import DB_PATH
from bot.database import list_rsvp_ids, mark_reminder_sent, meetings_for_reminder
from bot.meetings import format_when, format_place


async def send_due_reminders(bot: Bot) -> None:
    for kind, title in (("day", "Напоминание: завтра встреча INSTA CLUB"), ("hour", "Напоминание: встреча через 2 часа")):
        for meeting in meetings_for_reminder(DB_PATH, kind):
            text = (
                f"<b>{title}</b>\n\n"
                f"{format_place(meeting)}\n"
                f"Тема: {meeting.get('topic')}\n"
                f"Когда: {format_when(meeting['starts_at'])}"
            )
            for telegram_id in list_rsvp_ids(DB_PATH, int(meeting["id"])):
                try:
                    await bot.send_message(telegram_id, text)
                except Exception:
                    continue
            mark_reminder_sent(DB_PATH, int(meeting["id"]), kind)
            logging.info("Напоминание %s отправлено для встречи %s", kind, meeting["id"])


async def reminder_loop(bot: Bot) -> None:
    await asyncio.sleep(20)
    while True:
        try:
            await send_due_reminders(bot)
        except Exception:
            logging.exception("Ошибка цикла напоминаний")
        await asyncio.sleep(60)
