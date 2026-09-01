import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import bot.config as config
from bot.config import BOT_TOKEN, DB_PATH, db_is_persistent, is_railway, volume_mount_path
from bot.database import init_db
from bot.handlers import get_routers
from bot.notices import send_launch_notices
from bot.notify import notify_admins
from bot.reminders import reminder_loop

EPHEMERAL_DB_WARNING = (
    "⚠️ <b>INSTA CLUB — база не сохраняется</b>\n\n"
    "Сейчас SQLite лежит на временном диске контейнера. "
    "После Redeploy участники, заявки и встречи обнулятся.\n\n"
    "В Railway:\n"
    "1. Сервис бота → <b>Volumes</b> → Add Volume\n"
    "2. Mount path: <code>/data</code>\n"
    "3. Variables: <code>DB_PATH=/data/instaclub.db</code>\n"
    "4. Redeploy\n\n"
    f"Файл сейчас: <code>{DB_PATH}</code>"
)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    init_db(DB_PATH)
    persistent = db_is_persistent(DB_PATH)
    logging.info(
        "SQLite: %s | persistent=%s | railway=%s | volume=%s",
        DB_PATH,
        persistent,
        is_railway(),
        volume_mount_path() or "—",
    )
    if not persistent:
        logging.error(
            "База на временном диске. Добавьте Volume /data и DB_PATH=/data/instaclub.db"
        )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    me = await bot.get_me()
    if me.username:
        config.BOT_USERNAME = me.username
        logging.info("INSTA CLUB bot: @%s", me.username)

    if not persistent:
        await notify_admins(bot, EPHEMERAL_DB_WARNING)

    await send_launch_notices(bot)

    dp = Dispatcher(storage=MemoryStorage())
    for router in get_routers():
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(reminder_loop(bot))
    logging.info("INSTA CLUB запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
