"""
Обработчики команд напоминаний для бота Сумеречная Искорка.
Команды: /reminders, /cancel

Автор: MADAO81
Версия: 2.2 — исправлена ошибка Markdown
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
    logger.info("📋 Команда /reminders вызвана")

    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    user_id = update.effective_user.id
    chat_id = update.message.chat_id if update.message.chat.type != "private" else None

    logger.info(f"📋 user_id={user_id}, chat_id={chat_id}")

    reminders = reminder_manager.get_user_reminders(user_id, chat_id)

    if not reminders:
        await update.message.reply_text(
            "📋 У тебя нет активных напоминаний!\n\n"
            "Чтобы создать напоминание, напиши:\n"
            "напомни 15 июля в 14:00 позвонить клиенту\n\n"
            "А чтобы создать групповое напоминание, добавь слово 'групповое':\n"
            "напомни групповое завтра в 10:00 провести встречу"
        )
        return

    text = "📋 Твои активные напоминания:\n\n"
    for i, reminder in enumerate(reminders, 1):
        remind_at = reminder['remind_at']
        is_private = reminder.get('is_private', True)
        type_label = "🔒 Личное" if is_private else "📢 Групповое"
        text += f"{i}. {type_label} 🕐 {remind_at} — {reminder['text']}\n"
        if reminder.get('is_recurring'):
            text += f"   🔄 Повтор: {reminder['recurring_type']}\n"

    text += f"\nИтого: {len(reminders)} напоминаний"
    text += "\n\n❌ Чтобы отменить, напиши: отмени напоминание про ..."

    # Если пользователь в группе и есть личные напоминания — дублируем в личку
    if chat_id and any(r.get('is_private', True) for r in reminders):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text
            )
            await update.message.reply_text("📬 Я отправила тебе список твоих напоминаний в личку! 📚")
        except Exception as e:
            logger.error(f"❌ Не удалось отправить в личку: {e}")
            await update.message.reply_text(text)
    else:
        await update.message.reply_text(text)
