"""
Планировщик напоминаний для Сумеречной Искорки.
Отправляет напоминания в тот же чат, где они были созданы.

Автор: MADAO81
Версия: 2.1 — отправка в чат создания
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
    try:
        due_reminders = reminder_manager.get_due_reminders()
        if not due_reminders:
            return

        logger.info(f"⏰ Найдено {len(due_reminders)} напоминаний для отправки")

        for reminder in due_reminders:
            try:
                user_id = reminder['user_id']
                chat_id = reminder['chat_id']
                text = reminder['text']
                reminder_id = reminder['id']
                is_recurring = reminder['is_recurring']
                recurring_type = reminder.get('recurring_type')
                is_private = reminder.get('is_private', True)

                clean_text = text.replace("@twilight_sparkle_rus_bot", "").strip()

                response = (
                    f"📚 Напоминание от Сумеречной Искорки!\n\n"
                    f"⏰ Ты просил(а) напомнить:\n"
                    f"{clean_text}\n\n"
                    f"💪 Я верю в тебя — ты справишься! 📖✨"
                )

                # Отправляем в тот же чат, где было создано напоминание
                if is_private:
                    # Личное — пробуем отправить в личку
                    try:
                        await app.bot.send_message(
                            chat_id=user_id,
                            text=response
                        )
                        logger.info(f"✅ Личное напоминание #{reminder_id} отправлено пользователю {user_id}")
                    except Exception as e:
                        # Если не можем отправить в личку — отправляем в чат создания
                        logger.warning(f"⚠️ Не удалось отправить в личку #{reminder_id}: {e}")
                        await app.bot.send_message(
                            chat_id=chat_id,
                            text=response
                        )
                        logger.info(f"✅ Напоминание #{reminder_id} отправлено в чат {chat_id}")
                else:
                    # Групповое — в группу
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=response
                    )
                    logger.info(f"✅ Групповое напоминание #{reminder_id} отправлено в чат {chat_id}")

                # Отмечаем как отправленное
                reminder_manager.mark_sent(reminder_id)

                # Если повторяющееся — переносим
                if is_recurring and recurring_type:
                    reminder_manager.reschedule_recurring(reminder_id, recurring_type)

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
