"""
Административные команды для бота Сумеречная Искорка.

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config
from bot.utils.time_utils import is_working_hours

logger = logging.getLogger(__name__)

ADMIN_ID = int(Config.ADMIN_ID) if hasattr(Config, 'ADMIN_ID') and Config.ADMIN_ID else None


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для админ-панели."""
    if ADMIN_ID is None:
        await update.message.reply_text("❌ Администратор не настроен!")
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды!")
        return

    await update.message.reply_text(
        "🦄 *Админ-панель Сумеречной Искорки*\n\n"
        "🚧 В разработке...\n\n"
        "Здесь будет управление напоминаниями и рассылками.",
        parse_mode="Markdown"
    )
