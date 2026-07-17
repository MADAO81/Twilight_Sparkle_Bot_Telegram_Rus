"""
Планировщик напоминаний для Сумеречной Искорка.
Проверяет каждую минуту, не пора ли отправить напоминание.

Автор: MADAO81
Версия: 1.1 — отправка конкретному пользователю
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bot.core.reminder_manager import ReminderManager
from bot.services.ai_service import get_twilight_response

logger = logging.getLogger(__name__)

reminder_manager = ReminderManager()
scheduler = AsyncIOScheduler()


async def check_reminders(app):
    """Проверяет напоминания и отправляет те, которые наступили."""
    try:
        due_reminders = reminder_manager.get_due_reminders()

        if not due_reminders:
            return

        logger.info(f"⏰ Найдено {len(due_reminders)} напоминаний для отправки")

        for reminder in due_reminders:
            try:
                user_id = reminder['user_id']
                text = reminder['text']
                reminder_id = reminder['id']
                is_recurring = reminder['is_recurring']
                recurring_type = reminder.get('recurring_type')

                # Генерируем тёплое сообщение с напоминанием
                response = await get_twilight_response(
                    user_message=f"Напомни пользователю о деле: {text}. Сделай это мягко, но чётко. Обратись к нему по имени, если знаешь. Добавь пару ободряющих слов.",
                    mood_description="happy"
                )

                if not response:
                    response = f"📚 *Напоминание!*\n\n{text}\n\nНе забудь это сделать! 💜"

                # Отправляем личное сообщение пользователю
                await app.bot.send_message(
                    chat_id=user_id,
                    text=response,
                    parse_mode="Markdown"
                )

                logger.info(f"✅ Отправлено напоминание #{reminder_id} пользователю {user_id}")

                # Обработка после отправки
                if is_recurring and recurring_type:
                    success = reminder_manager.reschedule_recurring(reminder_id, recurring_type)
                    if success:
                        logger.info(f"🔄 Напоминание #{reminder_id} перенесено ({recurring_type})")
                    else:
                        reminder_manager.mark_sent(reminder_id)
                        logger.warning(f"⚠️ Не удалось перенести #{reminder_id}, деактивируем")
                else:
                    reminder_manager.mark_sent(reminder_id)
                    logger.info(f"🗑️ Напоминание #{reminder_id} деактивировано")

            except Exception as e:
                logger.error(f"❌ Ошибка отправки напоминания #{reminder_id}: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке напоминаний: {e}")


def start_reminder_scheduler(app):
    """Запускает планировщик напоминаний."""
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
        logger.error(f"❌ Ошибка при запуске планировщика напоминаний: {e}")


def stop_reminder_scheduler():
    """Останавливает планировщик напоминаний."""
    try:
        scheduler.shutdown()
        logger.info("⏹️ Планировщик напоминаний остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке планировщика: {e}")
