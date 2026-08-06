"""
AI сервис для бота Сумеречная Искорка.
Гибридный режим: DeepSeek (текст + поиск) + OpenAI (картинки + голос).

Автор: MADAO81
Версия: 2.3 — увеличен max_tokens для рассылок
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
            return response.choices[0].message.content.strip()
        return None

    except Exception as e:
        logger.error(f"❌ DeepSeek error: {e}")
        return None


async def get_daily_fact() -> Optional[str]:
    """Генерирует интересный факт дня на РУССКОМ языке."""
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/openrouter/v1"
        )

        prompt = "Расскажи короткий, интересный научный или исторический факт. ОБЯЗАТЕЛЬНО на русском языке. Будь остроумна и увлекательна, как Искорка. Ответ должен быть не слишком длинным — 3-4 предложения."
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await client.chat.completions.create(
            model=Config.DEEPSEEK_MODEL,
            messages=messages,
            max_tokens=500,  # Увеличено с 200 до 500
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        return None

    except Exception as e:
        logger.error(f"❌ Daily fact error: {e}")
        return None


async def get_goodnight_message() -> Optional[str]:
    """Генерирует пожелание спокойной ночи на РУССКОМ языке."""
    try:
        client = AsyncOpenAI(
            api_key=Config.PROXY_API_KEY,
            base_url="https://api.proxyapi.ru/openrouter/v1"
        )

        prompt = "Пожелай пользователю спокойной ночи. ОБЯЗАТЕЛЬНО на русском языке. Сделай это остроумно, но тепло. Ты — Искорка. Ответ должен быть коротким — 2-3 предложения."
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await client.chat.completions.create(
            model=Config.DEEPSEEK_MODEL,
            messages=messages,
            max_tokens=300,  # Увеличено с 200 до 300
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        return None

    except Exception as e:
        logger.error(f"❌ Goodnight message error: {e}")
        return None


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
            {"role": "system", "content": "Ты — Сумеречная Искорка. Используй веб-поиск, чтобы найти актуальную информацию по запросу пользователя. Отвечай кратко, но содержательно, с сарказмом. ОТВЕЧАЙ НА РУССКОМ ЯЗЫКЕ."},
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
