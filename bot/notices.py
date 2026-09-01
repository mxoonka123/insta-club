import asyncio
import logging

from aiogram import Bot

from bot.config import DB_PATH
from bot.database import (
    has_app_flag,
    list_started_telegram_ids,
    set_app_flag,
)
from bot import texts

logger = logging.getLogger(__name__)


async def _send_once(bot: Bot, telegram_id: int, text: str) -> bool:
    try:
        await bot.send_message(telegram_id, text)
        return True
    except Exception:
        logger.info("Notice not delivered to %s", telegram_id)
        return False


async def send_launch_notices(bot: Bot) -> None:
    if not has_app_flag(DB_PATH, texts.FLAG_NEW_ADMIN):
        set_app_flag(DB_PATH, texts.FLAG_NEW_ADMIN)
        ok = await _send_once(bot, texts.NEW_ADMIN_ID, texts.NOTICE_NEW_ADMIN)
        logger.info("New admin notice sent=%s id=%s", ok, texts.NEW_ADMIN_ID)

    if has_app_flag(DB_PATH, texts.FLAG_CLUB_UPDATE):
        return

    set_app_flag(DB_PATH, texts.FLAG_CLUB_UPDATE)
    recipients = list_started_telegram_ids(DB_PATH)
    sent = 0
    for telegram_id in recipients:
        if await _send_once(bot, telegram_id, texts.NOTICE_CLUB_UPDATE):
            sent += 1
        await asyncio.sleep(0.05)
    logger.info("Club update notice: %s/%s", sent, len(recipients))
