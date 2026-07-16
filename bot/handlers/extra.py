# bot/handlers/extra.py
"""
Дополнительные команды для бота Сумеречная Искорка.
Команды: /book, /spell, /goodnight

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import get_twilight_response
from bot.utils.time_utils import is_working_hours, get_working_status_message

logger = logging.getLogger(__name__)


async def book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /book command — рекомендация книги."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    args = context.args
    query = " ".join(args) if args else "интересную книгу"

    status_message = await update.message.reply_text("📖 Дай-ка подумать, что бы тебе посоветовать...")

    try:
        # Генерируем рекомендацию через OpenAI
        response = await get_twilight_response(
            user_message=f"Пользователь просит посоветовать книгу: {query}. Посоветуй книгу из мира MLP или классическую литературу, которая подходит под его запрос. Опиши книгу и объясни, почему она интересна.",
            mood_description="happy"
        )

        await status_message.delete()

        if response:
            await update.message.reply_text(
                f"📖 *Книжный совет от Искорки:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "😅 Ой! Я не смогла подобрать книгу... Попробуй ещё раз! 📚"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка в book_command: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так!\n"
            "Попробуй позже! 📚"
        )


async def spell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /spell command — магический совет."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    args = context.args
    query = " ".join(args) if args else "удачи"

    status_message = await update.message.reply_text("🔮 Сейчас я призову магию...")

    try:
        response = await get_twilight_response(
            user_message=f"Пользователь просит магический совет или заклинание на тему: {query}. Дай короткий, тёплый и вдохновляющий «магический совет» или «ритуал». Говори с лёгкой таинственностью, но по-дружески. Используй образы звёзд, книг, магии.",
            mood_description="happy"
        )

        await status_message.delete()

        if response:
            await update.message.reply_text(
                f"🔮 *Магический совет от Искорки:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔮 Заклинание не сработало... Попробуй ещё раз! 💫"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка в spell_command: {e}")
        await status_message.edit_text(
            "😅 Упс! Магия пошла не по плану!\n"
            "Попробуй позже! 🔮"
        )


async def goodnight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /goodnight command — пожелание спокойной ночи."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    status_message = await update.message.reply_text("✨ Сейчас я пожелаю тебе спокойной ночи...")

    try:
        response = await get_twilight_response(
            user_message="Пожелай пользователю спокойной ночи. Скажи что-то тёплое, уютное, как из книжной сказки. Используй образы звёзд, луны, снов. Добавь лёгкое, успокаивающее пожелание.",
            mood_description="happy"
        )

        await status_message.delete()

        if response:
            await update.message.reply_text(
                f"✨ *Спокойной ночи от Искорки:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "✨ Спокойной ночи! Пусть тебе приснятся хорошие сны! 🌙"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка в goodnight_command: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так!\n"
            "Спокойной ночи! 🌙"
        )