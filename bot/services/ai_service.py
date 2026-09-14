"""
AI сервис для бота Сумеречная Искорка.
Гибридный режим: DeepSeek (текст + поиск) + OpenAI (картинки + голос).

Автор: MADAO81
Версия: 2.4 — рассылки через общий механизм (фикс обрезки)
"""

import logging
import base64
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from bot.config import Config
from bot.core.constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def get_twilight_response(
    user_message: str,
    mood_description: str = "happy",
    context_history: Optional[List[Dict]] = None,
    use_search: bool = False
) -> Optional[str]:
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/openrouter/v1"
        )

        system_prompt = SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Your current mood is: {mood_description}"}
        ]

        if context_history:
            messages.extend(context_history[-10:])

        messages.append({"role": "user", "content": user_message})

        params = {
            "model": Config.DEEPSEEK_MODEL,
            "messages": messages,
            "max_tokens": Config.DEEPSEEK_MAX_TOKENS,
            "temperature": Config.DEEPSEEK_TEMPERATURE,
            "timeout": 30.0
        }

        if use_search:
            params["tools"] = [{"type": "web_search"}]
            logger.info("🌐 Добавлен инструмент веб-поиска")

        response = await client.chat.completions.create(**params)

        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            content = choice.message.content.strip() if choice.message.content else None

            if finish_reason == "length":
                logger.warning(
                    f"⚠️ Ответ обрезан по длине! finish_reason={finish_reason}, "
                    f"content_length={len(content) if content else 0}"
                )
            else:
                logger.debug(f"✅ Ответ получен. finish_reason={finish_reason}")

            return content
        return None

    except Exception as e:
        logger.error(f"❌ DeepSeek error: {e}")
        return None


async def get_daily_fact() -> Optional[str]:
    """
    Генерирует интересный факт дня на РУССКОМ языке.
    Использует общий механизм get_twilight_response, чтобы избежать обрезки.
    """
    user_message = (
        "Представь, что ты пишешь сообщение в чат для своих подписчиков. "
        "Это НЕ команда, а полноценный пост. Расскажи интересный научный или исторический факт. "
        "ОБЯЗАТЕЛЬНО на русском языке. Будь остроумна, увлекательна и в своём стиле — как Искорка. "
        "Сообщение должно быть ЗАКОНЧЕННЫМ — с началом, основной частью и концовкой. "
        "НЕ обрывай на полуслове. Пиши столько, сколько нужно, чтобы раскрыть факт интересно."
    )

    logger.info("📚 Генерация факта дня через get_twilight_response...")
    return await get_twilight_response(user_message, mood_description="happy")


async def get_goodnight_message() -> Optional[str]:
    """
    Генерирует пожелание спокойной ночи на РУССКОМ языке.
    Использует общий механизм get_twilight_response, чтобы избежать обрезки.
    """
    user_message = (
        "Представь, что ты пишешь вечернее сообщение в чат для своих подписчиков. "
        "Это НЕ команда, а полноценное пожелание спокойной ночи. "
        "Пожелай спокойной ночи остроумно, но тепло — в своём стиле, как Искорка. "
        "ОБЯЗАТЕЛЬНО на русском языке. "
        "Сообщение должно быть ЗАКОНЧЕННЫМ — с началом, основной частью и концовкой. "
        "НЕ обрывай на полуслове. Пиши столько, сколько нужно, чтобы получилось душевно."
    )

    logger.info("🌙 Генерация спокойной ночи через get_twilight_response...")
    return await get_twilight_response(user_message, mood_description="happy")


async def analyze_image(
    image_data: bytes,
    user_message: Optional[str] = None,
    mood_description: str = "happy"
) -> Optional[str]:
    logger.info("🖼️ Request to OpenAI Vision API...")
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/v1"
        )

        system_prompt = SYSTEM_PROMPT
        if mood_description == "sad":
            system_prompt += "\n\nYou are in a sad mood, but still trying to be kind."

        base64_image = base64.b64encode(image_data).decode('utf-8')

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"User sent an image. {user_message if user_message else 'Describe what you see in the image and comment on it in your style.'} ОТВЕЧАЙ НА РУССКОМ ЯЗЫКЕ."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        logger.info("🖼️ Sending request to OpenAI Vision API...")

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ Vision API returned empty response")
            return None

    except Exception as e:
        logger.error(f"❌ Error analyzing image: {e}")
        return None


async def transcribe_audio(
    audio_data: bytes,
    file_extension: str = ".ogg"
) -> Optional[str]:
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/v1"
        )

        audio_dir = Path(Config.AUDIO_DIR)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"voice_{int(time.time())}{file_extension}"
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        with open(audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        os.remove(audio_path)

        if transcription and transcription.text:
            return transcription.text.strip()
        return None

    except Exception as e:
        logger.error(f"❌ Whisper error: {e}")
        return None


async def search_web(query: str) -> Optional[str]:
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/openrouter/v1"
        )

        messages = [
            {"role": "system", "content": "Ты — Сумеречная Искорка. Используй веб-поиск, чтобы найти актуальную информацию по запросу пользователя. Отвечай содержательно, с сарказмом. ОТВЕЧАЙ НА РУССКОМ ЯЗЫКЕ."},
            {"role": "user", "content": query}
        ]

        response = await client.chat.completions.create(
            model=Config.DEEPSEEK_MODEL,
            messages=messages,
            tools=[{"type": "web_search"}],
            max_tokens=1000,
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        return None

    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return None
