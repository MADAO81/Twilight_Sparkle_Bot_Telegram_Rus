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
    logger.info("📸 НОВАЯ ВЕРСИЯ handle_photo ВЫЗВАНА!")

    if not is_working_hours():
        logger.info("⏰ Не рабочее время")
        return

    status_message = await update.message.reply_text("🖼️ Смотрю на картинку...")

    try:
        user_id = update.effective_user.id
        user_message = update.message.caption or "Без подписи"

        logger.info("📸 Шаг 1: Получаю фото...")
        photo_file = await update.message.photo[-1].get_file()
        
        logger.info("📸 Шаг 2: Скачиваю данные...")
        image_data = await photo_file.download_as_bytearray()
        
        logger.info(f"📸 Шаг 3: Фото получено, размер: {len(image_data)} байт")
        logger.info("📸 Шаг 4: Инициализация клиента через ProxyAPI...")

        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/v1"
        )
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        logger.info("📸 Шаг 5: Изображение закодировано")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": user_message or "Опиши картинку с сарказмом, как Искорка."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]

        logger.info("📸 Шаг 6: Отправка запроса в Vision через ProxyAPI...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.8,
            timeout=30.0
        )

        logger.info("📸 Шаг 7: Ответ получен")
        result = response.choices[0].message.content.strip() if response.choices else None
        logger.info(f"📸 Шаг 8: Результат: {result[:100] if result else 'None'}")

        if not result:
            result = "🖼️ Красивая картинка! 📚"

        await status_message.delete()
        await update.message.reply_text(f"🖼️ {result}")

        context_manager.save_context(user_id, f"[Фото] {user_message}", result)
        logger.info("✅ Фото обработано")

    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}")
        logger.error(f"❌ ТИП ОШИБКИ: {type(e)}")
        logger.error(f"❌ ТРЕЙСБЕК:\n{traceback.format_exc()}")
        await status_message.edit_text("🖼️ Ой! Что-то пошло не так! 📚")
