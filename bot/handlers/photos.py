"""
Обработчик фото для бота Сумеречная Искорка.
Комментирует фото ТОЛЬКО если в подписи есть вопрос или ключевые слова.

Автор: MADAO81
Версия: 2.3 — только по запросу
"""

import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.ai_service import analyze_image
from bot.utils.time_utils import is_working_hours
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

context_manager = ContextManager()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото — только если есть вопрос в подписи."""
    logger.info("📸 ФУНКЦИЯ handle_photo ВЫЗВАНА!")

    if not is_working_hours():
        logger.info("⏰ Не рабочее время, фото игнорируется")
        return

    # === ПРОВЕРКА: есть ли вопрос в подписи ===
    caption = update.message.caption or ""
    question_keywords = ["?", "что", "кто", "где", "когда", "почему", "зачем", "как", "расскажи", "опиши", "скажи"]
    is_question = any(kw in caption.lower() for kw in question_keywords)

    if not is_question:
        logger.info("📸 Нет вопроса в подписи, пропускаем")
        await update.message.reply_text("📸 Хочешь, чтобы я описала картинку? Спроси с вопросом! 😏")
        return

    status_message = await update.message.reply_text("🖼️ Смотрю на картинку...")

    try:
        user_id = update.effective_user.id
        user_message = caption or "Без подписи"

        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()

        logger.info(f"📸 Фото получено, размер: {len(image_data)} байт")

        response = await analyze_image(
            image_data=bytes(image_data),
            user_message=user_message,
            mood_description="happy"
        )

        if not response:
            response = "📸 Что-то я не разобрала картинку. Попробуй спросить по-другому! 📚"

        await status_message.delete()
        await update.message.reply_text(f"📸 {response}")

        context_manager.save_context(user_id, f"[Фото] {user_message}", response)
        logger.info("✅ Фото обработано успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото: {e}")
        await status_message.edit_text(
            "📸 Ой! Что-то пошло не так! Попробуй ещё раз! 📚"
        )
