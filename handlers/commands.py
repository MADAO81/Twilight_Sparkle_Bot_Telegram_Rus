# bot/handlers/commands.py
"""
Основные команды для бота Сумеречная Искорка.
Команды: /start, /help, /weather

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.weather_service import WeatherService
from bot.utils.time_utils import is_working_hours, get_working_status_message
from bot.core.constants import VERSION, COMMANDS

logger = logging.getLogger(__name__)

weather_service = WeatherService()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    text = (
        "📚 *Привет! Я Сумеречная Искорка!*\n\n"
        "✨ Я рада познакомиться с тобой! Я — ученица Принцессы Селестии, и моя страсть — книги, магия и организация всего на свете! 🦄\n\n"
        "📋 *Вот что я умею:*\n"
        "/help — список всех команд 📖\n"
        "/weather — погода 🌤️\n"
        "/book — посоветовать книгу 📖\n"
        "/spell — магический совет 🔮\n"
        "/goodnight — спокойной ночи ✨\n"
        "/reminders — список напоминаний 📋\n"
        "/cancel — отменить напоминание ❌\n"
        "/subscribe — подписаться на рассылки 📚\n"
        "/unsubscribe — отписаться\n"
        "/cleardata — очистить историю 🗑️\n\n"
        "🔒 *О данных:* Я сохраняю историю разговора только для поддержания беседы. "
        "Данные не передаются третьим лицам. Напиши /cleardata, чтобы удалить всю историю.\n\n"
        "💡 *Совет:* Просто напиши мне что-нибудь, и мы поболтаем! А если хочешь что-то запомнить — скажи «напомни...» и я всё запишу! 📚\n\n"
        f"🤖 *Версия:* {VERSION}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    text = (
        "📖 *Команды Сумеречной Искорки:*\n\n"
        "/start — начать общение 🌸\n"
        "/help — эта справка 📖\n"
        "/weather — погода 🌤️\n"
        "/book — посоветовать книгу по жанру 📖\n"
        "/spell — магический совет на удачу 🔮\n"
        "/goodnight — пожелание спокойной ночи ✨\n"
        "/reminders — список активных напоминаний 📋\n"
        "/cancel — отменить напоминание ❌\n"
        "/subscribe — подписаться на рассылки 📚\n"
        "/unsubscribe — отписаться от рассылок\n"
        "/cleardata — удалить историю диалога 🗑️\n\n"
        "🔒 *О данных:* Я сохраняю историю разговора только для поддержания беседы. "
        "Данные не передаются третьим лицам.\n\n"
        "✨ *Особенности:*\n"
        "• Я работаю с 9:00 до 20:00 ежедневно\n"
        "• Каждый день в 10:00 я присылаю интересный факт дня\n"
        "• Каждый день в 21:00 я желаю спокойной ночи\n"
        "• Я умею запоминать напоминания! Просто скажи «напомни...»\n"
        "• Я обожаю книги и всегда готова посоветовать что-то интересное\n\n"
        "💡 *Совет:* Просто напиши мне что-нибудь, и мы поболтаем!"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /weather command."""
    if not is_working_hours():
        if update.message.chat.type == "private":
            await update.message.reply_text(get_working_status_message())
        return

    args = context.args
    city = " ".join(args) if args else None

    status_message = await update.message.reply_text("🌤️ Смотрю в окно... Сейчас узнаю!")

    try:
        if city:
            weather = await weather_service.get_weather_by_city(city)
            if not weather:
                await status_message.edit_text(
                    f"😅 Не могу найти город '{city}'!\n"
                    "Проверь название или попробуй просто /weather для Ворсино 🌤️"
                )
                return
        else:
            weather = await weather_service.get_weather()

        if weather:
            weather_text = weather_service.get_weather_text(weather)

            details = (
                f"\n\n📊 *Подробнее:*\n"
                f"💧 Влажность: {weather.get('humidity', '?')}%\n"
                f"💨 Ветер: {weather.get('wind_speed', '?')} м/с\n"
                f"📈 Давление: {weather.get('pressure', '?')} мм рт. ст."
            )

            full_text = f"🌤️ *Погода*\n\n{weather_text}{details}"

            await status_message.delete()
            await update.message.reply_text(full_text, parse_mode="Markdown")
        else:
            await status_message.edit_text(
                "😅 Ой! Не могу узнать погоду!\n"
                "Попробуй позже! 🌧️"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка получения погоды: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так с погодой!\n"
            "Попробуй позже! 🌤️"
        )