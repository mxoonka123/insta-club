from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.community import router as community_router
from bot.handlers.events import router as events_router
from bot.handlers.knowledge import router as knowledge_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.payment import router as payment_router
from bot.handlers.profile import router as profile_router
from bot.handlers.referral import router as referral_router
from bot.handlers.start import router as start_router
from bot.handlers.subscription import router as subscription_router


def get_routers() -> list[Router]:
    return [
        admin_router,
        start_router,
        onboarding_router,
        payment_router,
        community_router,
        knowledge_router,
        events_router,
        subscription_router,
        referral_router,
        profile_router,
    ]
