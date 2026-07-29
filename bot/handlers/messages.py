"""
Обработчик текстовых сообщений для бота Сумеречная Искорка.
Реагирует на упоминания, распознаёт запросы на поиск и погоду.

Автор: MADAO81
Версия: 2.1 — расширены ключевые слова для поиска
"""

import logging
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from bot.services.ai_service import get_twilight_response, search_web
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

    # === ПРОВЕРКА: нужно ли реагировать ===
    if update.message.chat.type == "private":
        logger.info("📩 Сообщение в личке — отвечаем всегда")
    else:
        bot_username = context.bot.username
        message_text = update.message.text or ""
        logger.info(f"📩 Групповое сообщение: '{message_text[:50]}...'")

        if f"@{bot_username}" in message_text.lower():
            logger.info("✅ Найдено упоминание")
        else:
            logger.info("⏭️ Пропускаем сообщение в группе (нет упоминания)")
            return

    status_message = await update.message.reply_text("💭 Думаю...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.text or ""

        # ========== ПРОВЕРКА НА ВЕБ-ПОИСК ==========
        search_keywords = [
            "найди", "поищи", "погугли", "узнай",
            "расскажи", "что такое", "кто такой",
            "как работает", "последние новости",
            "новости", "свежие", "актуально",
            "информация о", "данные о", "расскажи про"
        ]
        if any(keyword in user_message.lower() for keyword in search_keywords):
            logger.info("🔍 Обнаружен запрос на поиск")
            response = await search_web(user_message)
            if response:
                await status_message.delete()
                await update.message.reply_text(f"🔍 *Результат поиска:*\n\n{response}", parse_mode="Markdown")
                return
            else:
                await status_message.delete()
                await update.message.reply_text("😅 Не смогла найти информацию. Попробуй переформулировать запрос! 📚")
                return

        # ========== ПРОВЕРКА НА СОЗДАНИЕ НАПОМИНАНИЯ ==========
        reminder_keywords = ["напомни", "напоминание", "напомнить", "запомни"]
        if any(keyword in user_message.lower() for keyword in reminder_keywords):
            logger.info("🔍 Обнаружена команда создания напоминания")
            parsed = reminder_parser.parse_reminder(user_message)
            if parsed:
                text, remind_at, is_recurring, recurring_type, is_private = parsed
                if remind_at < datetime.now() and not is_recurring:
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

                await status_message.delete()

                type_label = "🔒 Личное" if is_private else "📢 Групповое"
                type_desc = "в личку" if is_private else f"в группу {update.message.chat.title or 'эту группу'}"

                confirm_text = (
                    f"✅ *Напоминание сохранено!*\n\n"
                    f"📌 *Тип:* {type_label} (придёт {type_desc})\n"
                    f"📌 *Текст:* {text}\n"
                    f"🕐 *Время:* {remind_at.strftime('%d.%m.%Y в %H:%M')}"
                )
                if is_recurring:
                    confirm_text += f"\n🔄 *Повтор:* {recurring_type}"

                confirm_text += "\n\n📚 Я напомню тебе вовремя! 💜"

                await update.message.reply_text(confirm_text, parse_mode="Markdown")
                return
            else:
                await status_message.delete()
                await update.message.reply_text(
                    "😅 Не смогла разобрать дату и время!\n\n"
                    "Попробуй так:\n"
                    "`напомни 15 июля в 14:00 позвонить клиенту`\n"
                    "или\n"
                    "`напомни через 3 дня сдать отчёт`",
                    parse_mode="Markdown"
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
                success = reminder_manager.cancel_reminder_by_text(user_id, query, chat_id)
                await status_message.delete()
                if success:
                    await update.message.reply_text(f"✅ *Напоминание отменено!*")
                else:
                    await update.message.reply_text(f"❌ Не нашла напоминание по запросу: _{query}_")
                return

        # ========== ПРОВЕРКА НА ПОГОДУ ==========
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер"]
        if any(kw in user_message.lower() for kw in weather_keywords):
            logger.info("🔍 Обнаружен запрос погоды")
            weather = await weather_service.get_weather()
            if weather:
                weather_text = weather_service.get_weather_text(weather)
                await status_message.delete()
                await update.message.reply_text(f"🌤️ *Погода*\n\n{weather_text}", parse_mode="Markdown")
                return

        # ========== ОБЫЧНЫЙ ОТВЕТ ЧЕРЕЗ DEEPSEEK ==========
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
            logger.warning("⚠️ Не удалось удалить status_message")

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
