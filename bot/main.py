"""
Главный модуль бота Сумеречная Искорка.
Инициализация, настройка и запуск бота.

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from bot.config import Config
from bot.handlers.commands import start, help_command, weather_command
from bot.handlers.extra import book_command, spell_command, goodnight_command
from bot.handlers.reminders import reminders_command, cancel_reminder_command
from bot.handlers.messages import handle_message
from bot.handlers.photos import handle_photo
from bot.handlers.voice import handle_voice
from bot.handlers.admin import admin_panel
from bot.core.scheduler import start_scheduler, add_chat, remove_chat
from bot.core.reminder_scheduler import start_reminder_scheduler
from bot.core.constants import VERSION

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if Config.DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("🐛 DEBUG_MODE включён")


def main():
    """Точка входа в приложение."""
    logger.info(f"🦄 Запуск бота Сумеречная Искорка (v{VERSION})...")
    logger.info(f"👤 Автор: MADAO81")

    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN не найден в .env файле!")
        return

    if not Config.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY не найден в .env файле!")
        return

    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Автоматическая загрузка подписок из .env
    default_chats = getattr(Config, 'DEFAULT_CHATS', "")
    if default_chats:
        for chat_id in default_chats.split(","):
            try:
                chat_id = int(chat_id.strip())
                add_chat(chat_id)
                logger.info(f"✅ Автоматически добавлен чат: {chat_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка добавления чата {chat_id}: {e}")

    # ===== КОМАНДЫ =====
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("book", book_command))
    app.add_handler(CommandHandler("spell", spell_command))
    app.add_handler(CommandHandler("goodnight", goodnight_command))
    app.add_handler(CommandHandler("reminders", reminders_command))
    app.add_handler(CommandHandler("cancel", cancel_reminder_command))
    app.add_handler(CommandHandler("subscribe", add_chat))
    app.add_handler(CommandHandler("unsubscribe", remove_chat))
    app.add_handler(CommandHandler("admin", admin_panel))

    # ===== ОБРАБОТЧИКИ =====
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_voice))

    # ===== ПЛАНИРОВЩИКИ =====
    start_scheduler(app)
    start_reminder_scheduler(app)

    logger.info("✅ Бот успешно запущен и готов к работе!")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
