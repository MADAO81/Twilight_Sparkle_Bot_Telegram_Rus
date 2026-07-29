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


async def get_all_members(bot, chat_id: int, bot_username: str) -> list:
    """Получает реальных участников группы (без бота)."""
    members = []
    try:
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            user = admin.user
            if user.username == bot_username:
                continue
            name = user.first_name or user.username
            if name and name not in members:
                members.append(name)
        logger.info(f"👥 Получено {len(members)} реальных участников")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить участников: {e}")

    # Если список пуст — возвращаем пустой список, а не запасной
    return members


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if f"@{bot_username}" in message_text.lower():
            logger.info("✅ Найдено упоминание")
        else:
            logger.info("⏭️ Пропускаем сообщение в группе (нет упоминания)")
            return

    status_message = await update.message.reply_text("💭 Думаю...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.text or ""

        # === ОПРЕДЕЛЯЕМ, ВОПРОС ПРО ВЫБОР ===
        is_selection_question = any(keyword in user_message.lower() for keyword in [
            "кто", "какой", "выбери", "выбрать", "лучше", "умнее", "красивее", "круче"
        ])

        chat_users = []
        if update.message.chat.type != "private" and is_selection_question:
            chat_id = update.message.chat_id
            bot_username = context.bot.username
            chat_users = await get_all_members(context.bot, chat_id, bot_username)
            logger.info(f"👥 Передаю реальных участников: {chat_users}")

            # Если список пуст — не передаём ничего
            if not chat_users:
                await status_message.delete()
                await update.message.reply_text("😅 Не вижу других участников, чтобы выбрать!")
                return

        # === ПРОВЕРКА НА ПОИСК ===
        search_keywords = ["найди", "поищи", "погугли", "узнай", "расскажи", "что такое", "кто такой", "как работает", "последние новости", "новости", "свежие", "актуально"]
        if any(keyword in user_message.lower() for keyword in search_keywords):
            logger.info("🔍 Запрос на поиск")
            response = await search_web(user_message)
            if response:
                await status_message.delete()
                await update.message.reply_text(f"🔍 *Результат поиска:*\n\n{response}", parse_mode="Markdown")
                return
            else:
                await status_message.delete()
                await update.message.reply_text("😅 Не смогла найти информацию. Попробуй переформулировать! 📚")
                return

        # ========== НАПОМИНАНИЯ ==========
        reminder_keywords = ["напомни", "напоминание", "напомнить", "запомни"]
        if any(keyword in user_message.lower() for keyword in reminder_keywords):
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

        # ========== ОТМЕНА НАПОМИНАНИЯ ==========
        cancel_keywords = ["отмени напоминание", "удали напоминание", "отмени"]
        if any(keyword in user_message.lower() for keyword in cancel_keywords):
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

        # ========== ПОГОДА ==========
        weather_keywords = ["погода", "weather", "за окном", "температура", "дождь", "солнце", "градус", "ветер"]
        if any(kw in user_message.lower() for kw in weather_keywords):
            weather = await weather_service.get_weather()
            if weather:
                weather_text = weather_service.get_weather_text(weather)
                await status_message.delete()
                await update.message.reply_text(f"🌤️ *Погода*\n\n{weather_text}", parse_mode="Markdown")
                return

        # ========== ОБЫЧНЫЙ ОТВЕТ ==========
        context_history = context_manager.get_context(user_id)

        enhanced_message = user_message
        if chat_users:
            enhanced_message = f"{user_message}\n\n[Имена всех участников группы: {', '.join(chat_users)}]"

        response = await get_twilight_response(
            user_message=enhanced_message,
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
