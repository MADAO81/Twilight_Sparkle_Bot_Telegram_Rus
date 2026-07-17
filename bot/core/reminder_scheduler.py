import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bot.core.reminder_manager import ReminderManager

logger = logging.getLogger(__name__)

reminder_manager = ReminderManager()
scheduler = AsyncIOScheduler()


async def check_reminders(app):
    try:
        due_reminders = reminder_manager.get_due_reminders()
        if not due_reminders:
            return

        logger.info(f"⏰ Найдено {len(due_reminders)} напоминаний для отправки")

        for reminder in due_reminders:
            try:
                user_id = reminder['user_id']  # Отправляем в личку пользователя
                text = reminder['text']
                reminder_id = reminder['id']
                is_recurring = reminder['is_recurring']
                recurring_type = reminder.get('recurring_type')

                # Очищаем текст от @упоминаний бота
                clean_text = text.replace("@twilight_sparkle_rus_bot", "").strip()

                response = (
                    f"📚 *Напоминание от Сумеречной Искорки!*\n\n"
                    f"⏰ *Ты просил(а) напомнить:*\n"
                    f"_{clean_text}_\n\n"
                    f"💪 Я верю в тебя — ты справишься! 📖✨"
                )

                await app.bot.send_message(
                    chat_id=user_id,  # Отправляем в личку
                    text=response,
                    parse_mode="Markdown"
                )

                logger.info(f"✅ Отправлено напоминание #{reminder_id} пользователю {user_id}")

                if is_recurring and recurring_type:
                    reminder_manager.reschedule_recurring(reminder_id, recurring_type)
                else:
                    reminder_manager.mark_sent(reminder_id)

            except Exception as e:
                logger.error(f"❌ Ошибка отправки напоминания #{reminder_id}: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке напоминаний: {e}")


def start_reminder_scheduler(app):
    try:
        scheduler.add_job(
            check_reminders,
            IntervalTrigger(minutes=1),
            args=[app],
            id='reminder_check',
            replace_existing=True
        )
        scheduler.start()
        logger.info("✅ Планировщик напоминаний запущен (проверка каждую минуту)")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске планировщика: {e}")


def stop_reminder_scheduler():
    try:
        scheduler.shutdown()
        logger.info("⏹️ Планировщик напоминаний остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке планировщика: {e}")
