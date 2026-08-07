import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import bot.config as config
from bot.config import BOT_TOKEN, DB_PATH
from bot.database import init_db
from bot.handlers import get_routers


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    init_db(DB_PATH)
    logging.info("База данных инициализирована: %s", DB_PATH)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    me = await bot.get_me()
    if me.username:
        config.BOT_USERNAME = me.username
        logging.info("Бот: @%s", me.username)

    dp = Dispatcher(storage=MemoryStorage())
    for router in get_routers():
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("INSTA CLUB bot запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
