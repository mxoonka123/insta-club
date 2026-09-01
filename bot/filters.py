from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import ADMIN_IDS


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if user is None and isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        return bool(user and user.id in ADMIN_IDS)
