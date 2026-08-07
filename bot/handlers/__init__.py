from aiogram import Router

from bot.handlers.profile import router as profile_router
from bot.handlers.start import router as start_router


def get_routers() -> list[Router]:
    return [start_router, profile_router]
