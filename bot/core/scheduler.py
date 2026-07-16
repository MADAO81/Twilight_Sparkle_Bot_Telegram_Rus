# bot/core/scheduler.py
"""
Планировщик для бота Сумеречная Искорка.
Отправка факта дня в 10:00 и спокойной ночи в 21:00.

Автор: MADAO81
Версия: 1.0
"""

import logging
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.config import Config
from bot.services.ai_service import get_daily_fact, get_goodnight_message

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

DB_PATH = Config.DATA_DIR / "subscriptions.db"


def _get_connection():
    return sqlite3.connect(DB_PATH)


def _init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            chat_id INTEGER PRIMARY KEY,
            subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_chat(chat_id: int):
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscriptions (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"📋 Чат {chat_id} добавлен для рассылки")


def remove_chat(chat_id: int):
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"📋 Чат {chat_id} удалён из рассылки")


def get_active_chats():
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscriptions")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


async def send_daily_fact(app):
    """Отправляет факт дня в 10:00."""
    active_chats = get_active_chats()
    if not active_chats:
        logger.info("📭 Нет активных чатов для факта дня")
        return

    logger.info(f"📚 Отправка факта дня в {len(active_chats)} чатов...")

    fact = await get_daily_fact()
    if not fact:
        fact = "📚 *Факт дня:* Сегодня я узнала, что книги — лучшие друзья пони! Читайте больше! 📖"

    for chat_id in active_chats:
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=fact,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Факт дня отправлен в чат {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в чат {chat_id}: {e}")
            if "bot was blocked" in str(e) or "chat not found" in str(e):
                remove_chat(chat_id)


async def send_goodnight(app):
    """Отправляет пожелание спокойной ночи в 21:00."""
    active_chats = get_active_chats()
    if not active_chats:
        logger.info("📭 Нет активных чатов для пожелания спокойной ночи")
        return

    logger.info(f"🌙 Отправка спокойной ночи в {len(active_chats)} чатов...")

    message = await get_goodnight_message()
    if not message:
        message = "✨ *Спокойной ночи!* Пусть тебе приснятся самые удивительные сны, полные магии и дружбы! 🌙"

    for chat_id in active_chats:
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Спокойной ночи отправлена в чат {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в чат {chat_id}: {e}")
            if "bot was blocked" in str(e) or "chat not found" in str(e):
                remove_chat(chat_id)


def start_scheduler(app):
    """Запускает планировщик рассылок."""
    try:
        _init_db()

        # Автоматическая загрузка подписок из .env
        default_chats = Config.DEFAULT_CHATS if hasattr(Config, 'DEFAULT_CHATS') else ""
        if default_chats:
            for chat_id in default_chats.split(","):
                try:
                    chat_id = int(chat_id.strip())
                    add_chat(chat_id)
                    logger.info(f"✅ Автоматически добавлен чат: {chat_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка добавления чата {chat_id}: {e}")

        # Факт дня в 10:00
        scheduler.add_job(
            send_daily_fact,
            CronTrigger(hour=10, minute=0),
            args=[app],
            id='daily_fact',
            replace_existing=True
        )

        # Спокойной ночи в 21:00
        scheduler.add_job(
            send_goodnight,
            CronTrigger(hour=21, minute=0),
            args=[app],
            id='goodnight',
            replace_existing=True
        )

        scheduler.start()
        logger.info("✅ Планировщик рассылок запущен. Факт дня в 10:00, спокойной ночи в 21:00")

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске планировщика: {e}")


def stop_scheduler():
    """Останавливает планировщик рассылок."""
    try:
        scheduler.shutdown()
        logger.info("⏹️ Планировщик рассылок остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке планировщика: {e}")