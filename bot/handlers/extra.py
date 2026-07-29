"""
Дополнительные команды для бота Сумеречная Искорка.
Команды: /search, /book, /spell, /goodnight

Автор: MADAO81
Версия: 2.0 — DeepSeek + веб-поиск
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import get_twilight_response, search_web
from bot.utils.time_utils import is_working_hours, get_working_status_message

logger = logging.getLogger(__name__)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /search command — поиск в интернете."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "🌐 *Как выполнить поиск:*\n\n"
            "`/search что ты хочешь найти`\n\n"
            "Например:\n"
            "`/search последние новости науки`\n"
            "`/search кто такой Альберт Эйнштейн`",
            parse_mode="Markdown"
        )
        return

    query = " ".join(args)
    status_message = await update.message.reply_text("🔍 Ищу в интернете... Это может занять пару секунд! 🌐")

    try:
        response = await search_web(query)
        if response:
            await status_message.delete()
            await update.message.reply_text(
                f"🌐 *Результат поиска:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await status_message.edit_text("😅 Не нашла ничего по твоему запросу. Попробуй переформулировать! 📚")
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        await status_message.edit_text("😅 Ошибка при поиске! Попробуй позже.")


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
        response = await get_twilight_response(
            user_message=f"Пользователь просит посоветовать книгу: {query}. Ты — Искорка. Посоветуй книгу из мира MLP или классику. Будь остроумна.",
            mood_description="happy"
        )

        await status_message.delete()
        if response:
            await update.message.reply_text(
                f"📚 *Книжный совет от Искорки:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("😅 Не смогла подобрать книгу... Попробуй ещё раз! 📚")
    except Exception as e:
        logger.error(f"❌ Book error: {e}")
        await status_message.edit_text("😅 Ошибка! Попробуй позже.")


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
            user_message=f"Пользователь просит магический совет на тему: {query}. Дай короткий, остроумный совет с намёком на магию.",
            mood_description="happy"
        )

        await status_message.delete()
        if response:
            await update.message.reply_text(
                f"🔮 *Магический совет от Искорки:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("🔮 Заклинание не сработало... Попробуй ещё раз! 💫")
    except Exception as e:
        logger.error(f"❌ Spell error: {e}")
        await status_message.edit_text("😅 Ошибка! Попробуй позже.")


async def goodnight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /goodnight command — пожелание спокойной ночи."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    status_message = await update.message.reply_text("✨ Сейчас я пожелаю тебе спокойной ночи...")

    try:
        response = await get_twilight_response(
            user_message="Пожелай пользователю спокойной ночи. Сделай это остроумно, но тепло. Ты — Искорка.",
            mood_description="happy"
        )

        await status_message.delete()
        if response:
            await update.message.reply_text(
                f"🌙 *Спокойной ночи от Искорки:*\n\n{response}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("✨ Спокойной ночи! Пусть тебе приснятся хорошие сны! 🌙")
    except Exception as e:
        logger.error(f"❌ Goodnight error: {e}")
        await status_message.edit_text("😅 Ошибка! Попробуй позже.")
