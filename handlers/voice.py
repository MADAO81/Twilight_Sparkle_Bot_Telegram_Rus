# bot/handlers/voice.py
"""
Обработчик голосовых сообщений для бота Сумеречная Искорка.

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import transcribe_audio, get_twilight_response
from bot.utils.time_utils import is_working_hours
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

context_manager = ContextManager()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка голосовых сообщений."""
    if not is_working_hours():
        return

    status_message = await update.message.reply_text("🎧 Слушаю тебя... Подожди немного!")

    try:
        user_id = update.effective_user.id

        voice = update.message.voice
        file = await voice.get_file()
        audio_data = await file.download_as_bytearray()

        logger.info(f"🎤 Голосовое получено, размер: {len(audio_data)} байт")

        transcript = await transcribe_audio(
            audio_data=bytes(audio_data),
            file_extension=".ogg"
        )

        if not transcript:
            await status_message.edit_text(
                "😅 Ой-ой! Я не смогла разобрать, что ты сказал(а)!\n"
                "Попробуй говорить чётче или напиши текстом! 📚"
            )
            return

        logger.info(f"✅ Транскрипция: {transcript[:100]}...")

        context_history = context_manager.get_context(user_id)

        response = await get_twilight_response(
            user_message=transcript,
            mood_description="happy",
            context_history=context_history
        )

        if not response:
            response = "😅 Ой-ой! Что-то у меня мозги закипели!\nДавай попробуем ещё раз? 📚"

        await status_message.delete()

        reply_text = f"🎤 *Вы сказали:* _{transcript[:100]}..._\n\n{response}"

        if update.message.chat.type == "private":
            await update.message.reply_text(reply_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                reply_text,
                parse_mode="Markdown",
                reply_to_message_id=update.message.message_id
            )

        context_manager.save_context(user_id, transcript, response)
        logger.info("✅ Голосовое обработано успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка обработки голосового: {e}")
        await status_message.edit_text(
            "😅 Упс! Что-то пошло не так при обработке голосового!\n"
            "Попробуй ещё раз или напиши текстом! 📚"
        )