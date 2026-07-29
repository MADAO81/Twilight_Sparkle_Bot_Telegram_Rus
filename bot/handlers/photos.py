import logging
import base64
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from openai import AsyncOpenAI
from bot.config import Config
from bot.core.constants import SYSTEM_PROMPT
from bot.utils.time_utils import is_working_hours
from bot.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

context_manager = ContextManager()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📸 ФУНКЦИЯ handle_photo ВЫЗВАНА!")

    if not is_working_hours():
        logger.info("⏰ Не рабочее время")
        return

    status_message = await update.message.reply_text("🖼️ Смотрю на картинку...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.caption or "Красивая картинка!"

        # Получаем фото в максимальном качестве
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()
        
        logger.info(f"📸 Фото получено, размер: {len(image_data)} байт")

        # === ПРЯМОЙ OPENAI ===
        logger.info("🖼️ Отправка запроса в OpenAI Vision...")
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Кодируем изображение в base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        logger.info(f"🖼️ Изображение закодировано, длина: {len(base64_image)}")
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": user_message or "Опиши эту картинку."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }}
            ]}
        ]

        logger.info("🖼️ Вызов OpenAI...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.8,
            timeout=30.0
        )

        result = response.choices[0].message.content.strip() if response.choices else None
        logger.info(f"🖼️ Ответ получен: {result[:100] if result else 'None'}")

        if not result:
            result = "🖼️ Красивая картинка! 📚"

        await status_message.delete()

        if update.message.chat.type == "private":
            await update.message.reply_text(f"🖼️ {result}")
        else:
            await update.message.reply_text(
                f"🖼️ {result}",
                reply_to_message_id=update.message.message_id
            )

        context_manager.save_context(user_id, f"[Фото] {user_message}", result)
        logger.info("✅ Фото обработано")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        logger.error(f"❌ Трейсбек:\n{traceback.format_exc()}")
        await status_message.edit_text(
            "🖼️ Ой! Что-то пошло не так! 📚"
        )
