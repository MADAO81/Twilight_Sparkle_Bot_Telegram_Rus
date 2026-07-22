"""
Обработчик текстовых сообщений для бота Сумеречная Искорка.
Реагирует на упоминания, распознаёт напоминания и погоду.
Поддерживает личные и групповые напоминания.

Автор: MADAO81
Версия: 2.7 — исправлена ошибка Markdown
"""

import logging
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from bot.services.ai_service import get_twilight_response
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.context_manager import ContextManager
from bot.core.reminder_manager import ReminderManager
from bot.core.reminder_parser import ReminderParser

logger = logging.getLogger(__name__)

weather_service = WeatherService()
context_manager = ContextManager()
reminder_manager = ReminderManager()
reminder_parser = ReminderParser()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений."""
    logger.info("🔥 handle_message ВЫЗВАНА!")

    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    if update.message.chat.type == "private":
        logger.info("📩 Сообщение в личке — отвечаем всегда")
    else:
        bot_username = context.bot.username
        message_text = update.message.text or ""

        logger.info(f"📩 Групповое сообщение: '{message_text[:50]}...'")

        is_mentioned = False

        if f"@{bot_username}" in message_text.lower():
            is_mentioned = True
            logger.info("✅ Найдено упоминание @username")

        if update.message.reply_to_message:
            if update.message.reply_to_message.from_user.username == bot_username:
                is_mentioned = True
                logger.info("✅ Ответ на сообщение бота")

        if not is_mentioned:
            logger.info("⏭️ Пропускаем сообщение в группе (нет упоминания)")
            return

    status_message = await update.message.reply_text("💭 Думаю...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.text or ""

        logger.info(f"📩 Обработка сообщения от {user_id}: {user_message[:50]}...")

        # ========== ПРОВЕРКА НА СОЗДАНИЕ НАПОМИНАНИЯ ==========
        reminder_keywords = ["напомни", "напоминание", "напомнить", "запомни"]
        if any(keyword in user_message.lower() for keyword in reminder_keywords):
            logger.info("🔍 Обнаружена команда создания напоминания")
            parsed = reminder_parser.parse_reminder(user_message)
            logger.info(f"🔍 Результат парсинга: {parsed}")
            if parsed:
                text, remind_at, is_recurring, recurring_type, is_private = parsed
                logger.info(f"🔍 Распарсено: text='{text}', remind_at={remind_at}")

                if remind_at < datetime.now():
                    remind_at = remind_at + timedelta(days=1)
                    await update.message.reply_text(
                        f"⏰ Время уже прошло, перенесла на завтра: {remind_at.strftime('%d.%m.%Y в %H:%M')}\nПродолжаем? 💜"
                    )

                reminder_id = reminder_manager.add_reminder(
                    user_id=user_id,
                    chat_id=update.message.chat_id,
                    text=text,
                    remind_at=remind_at,
                    is_recurring=is_recurring,
                    recurring_type=recurring_type,
                    is_private=is_private
                )

                logger.info(f"✅ Напоминание #{reminder_id} создано")

                await status_message.delete()

                type_label = "Личное" if is_private else "Групповое"
                type_desc = "в личку" if is_private else f"в группу {update.message.chat.title or 'эту группу'}"

                confirm_text = (
                    f"✅ Напоминание сохранено!\n"
                    f"Тип: {type_label} (придёт {type_desc})\n"
                    f"Текст: {text}\n"
                    f"Время: {remind_at.strftime('%d.%m.%Y в %H:%M')}"
                )

                if is_recurring:
                    confirm_text += f"\nПовтор: "
                    if recurring_type == "daily":
                        confirm_text += "ежедневно"
                    elif recurring_type == "weekly":
                        confirm_text += "еженедельно"
                    elif recurring_type == "monthly":
                        confirm_text += "ежемесячно"

                confirm_text += "\n\nЯ напомню тебе вовремя! 💜"

                await update.message.reply_text(confirm_text)
                return
            else:
                await status_message.delete()
                await update.message.reply_text(
                    "😅 Не смогла разобрать дату и время!\n\n"
                    "Попробуй так:\n"
                    "напомни 15 июля в 14:00 позвонить клиенту\n"
                    "или\n"
                    "напомни через 3 дня сдать отчёт\n\n"
                    "Чтобы создать групповое напоминание, добавь слово 'групповое':\n"
                    "напомни групповое завтра в 10:00 провести встречу"
                )
                return

        # ========== ПРОВЕРКА НА ОТМЕНУ НАПОМИНАНИЯ ==========
        cancel_keywords = ["отмени напоминание", "удали напоминание", "отмени"]
        if any(keyword in user_message.lower() for keyword in cancel_keywords):
            logger.info("🔍 Обнаружена команда отмены")
            query = user_message
            for kw in cancel_keywords:
                query = query.lower().replace(kw, "").strip()
            if query:
                chat_id = update.message.chat_id if update.message.chat.type != "private" else None
                logger.info(f"🔍 Отмена: user_id={user_id}, query='{query}', chat_id={chat_id}")
                success = reminder_manager.cancel_reminder_by_text(user_id, query, chat_id)
                await status_message.delete()
                if success:
                    await update.message.reply_text(
                        f"✅ Напоминания отменены!\n\nПо запросу: {query}\n\nВсе подходящие напоминания удалены. 📚"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Не нашла напоминаний по запросу: {query}\n\nПроверь список командой /reminders"
                    )
                return

        # ========== ОБЫЧНЫЙ ОТВЕТ ==========
        logger.info("🔍 Обычный запрос, отправляем в OpenAI")
        context_history = context_manager.get_context(user_id)

        response = await get_twilight_response(
            user_message=user_message,
            mood_description="happy",
            context_history=context_history
        )

        if not response:
            response = "😅 Ой-ой! Что-то я задумалась... Давай попробуем ещё раз? 📚"

        try:
            await status_message.delete()
        except BadRequest:
            logger.warning("⚠️ Не удалось удалить status_message, возможно, его уже нет")

        await update.message.reply_text(response)

        context_manager.save_context(user_id, user_message, response)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        try:
            await status_message.edit_text(
                "😅 Упс! Что-то пошло не так!\nПопробуй ещё раз или напиши /help для справки! 📚"
            )
        except BadRequest:
            await update.message.reply_text(
                "😅 Упс! Что-то пошло не так!\nПопробуй ещё раз или напиши /help для справки! 📚"
            )
