from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import ADMIN_IDS, DB_PATH
from bot.database import admin_stats

router = Router(name="admin")


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not message.from_user or message.from_user.id not in ADMIN_IDS:
        await message.answer("Команда доступна только администраторам.")
        return

    stats = admin_stats(DB_PATH)
    lines = [
        "<b>Админ-панель INSTA CLUB</b>",
        f"Участников: {stats['total']}",
        "",
        "<b>По городам</b>",
    ]
    for row in stats["by_city"]:
        lines.append(f"• {row['city']}: {row['c']}")

    lines.append("")
    lines.append("<b>По нишам</b>")
    for row in stats["by_niche"]:
        lines.append(f"• {row['niche']}: {row['c']}")

    lines.append("")
    lines.append(
        "Полная админка (заявки, оплаты, рассылки, CRM) — следующий этап."
    )
    await message.answer("\n".join(lines))
