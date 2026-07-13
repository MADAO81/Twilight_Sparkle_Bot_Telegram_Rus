# bot/handlers/reminders.py
"""
Обработчики команд напоминаний для бота Сумеречная Искорка.
Команды: /reminders, /cancel

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.reminder_manager import ReminderManager
from bot.utils.time_utils import is_working_hours, get_working_status_message

logger = logging.getLogger(__name__)

reminder_manager = ReminderManager()


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /reminders command — список напоминаний."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    user_id = update.effective_user.id
    reminders = reminder_manager.get_user_reminders(user_id)

    if not reminders:
        await update.message.reply_text(
            "📋 *У тебя нет активных напоминаний!*\n\n"
            "Чтобы создать напоминание, просто напиши:\n"
            "`напомни 15 июля в 14:00 позвонить клиенту`\n\n"
            "Или:\n"
            "`напомни через 3 дня сдать отчёт`",
            parse_mode="Markdown"
        )
        return

    text = "📋 *Твои активные напоминания:*\n\n"
    for i, reminder in enumerate(reminders, 1):
        remind_at = reminder['remind_at']
        text += f"{i}. 🕐 {remind_at} — {reminder['text']}\n"
        if reminder['is_recurring']:
            text += f"   🔄 Повтор: {reminder['recurring_type']}\n"

    text += f"\n*Итого:* {len(reminders)} напоминаний"
    text += "\n\n❌ Чтобы отменить, напиши: `отмени напоминание про ...`"

    await update.message.reply_text(text, parse_mode="Markdown")


async def cancel_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /cancel command — отмена напоминания."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ *Как отменить напоминание:*\n\n"
            "Напиши: `/cancel текст напоминания`\n\n"
            "Или просто напиши в чат:\n"
            "`отмени напоминание про отчёт`",
            parse_mode="Markdown"
        )
        return

    user_id = update.effective_user.id
    query = " ".join(args)

    success = reminder_manager.cancel_reminder_by_text(user_id, query)

    if success:
        await update.message.reply_text(
            f"✅ *Напоминание отменено!*\n\n"
            f"Текст: _{query}_\n\n"
            "Можешь создать новое в любое время! 📚",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Не нашла напоминание с текстом: _{query}_\n\n"
            "Проверь список командой /reminders",
            parse_mode="Markdown"
        )