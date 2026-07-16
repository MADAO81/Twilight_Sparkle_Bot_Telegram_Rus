# bot/handlers/photos.py
"""
Обработчик фото для бота Сумеречная Искорка.

Автор: MADAO81
Версия: 1.0
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import analyze_image
from bot.utils.time_utils import is_working_hours
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

context_manager = ContextManager()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото."""
    if not is_working_hours():
        return

    status_message = await update.message.reply_text("🖼️ Смотрю на картинку... Сейчас что-то придумаю!")

    try:
        user_id = update.effective_user.id
        user_message = update.message.caption or "Красивая картинка!"

        # Получаем фото в максимальном качестве
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()

        logger.info(f"📸 Фото получено, размер: {len(image_data)} байт")

        # Анализируем изображение через Vision API
        response = await analyze_image(
            image_data=bytes(image_data),
            user_message=user_message,
            mood_description="happy"
        )

        if not response:
            response = "🖼️ Ой, какая красивая картинка! 📚"

        await status_message.delete()

        logger.info(f"📤 Отправлен ответ пользователю: {response[:100] if response else 'None'}")

        if update.message.chat.type == "private":
            await update.message.reply_text(f"🖼️ {response}")
        else:
            await update.message.reply_text(
                f"🖼️ {response}",
                reply_to_message_id=update.message.message_id
            )

        context_manager.save_context(user_id, f"[Фото] {user_message}", response)
        logger.info("✅ Фото обработано успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото: {e}")
        await status_message.edit_text(
            "🖼️ Ой, какая красивая картинка! "
            "Жаль, что я немного ослепла от такого великолепия! 📚"
        )