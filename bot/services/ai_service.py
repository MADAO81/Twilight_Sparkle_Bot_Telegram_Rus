# bot/services/ai_service.py
"""
AI сервис для бота Сумеречная Искорка (OpenAI GPT-4-turbo, Vision, Whisper).

Автор: MADAO81
Версия: 1.0
"""

import logging
import base64
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from bot.config import Config
from bot.core.constants import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def get_twilight_response(
    user_message: str,
    mood_description: str = "happy",
    context_history: Optional[List[Dict]] = None
) -> Optional[str]:
    """
    Генерирует ответ от Сумеречной Искорки через OpenAI.
    """
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        system_prompt = SYSTEM_PROMPT

        # Добавляем модификатор для настроения (если понадобится)
        if mood_description == "sad":
            system_prompt += """

            ⚠️ IMPORTANT: YOU ARE IN A SAD MOOD RIGHT NOW!
            - Speak more softly and thoughtfully
            - Use fewer exclamation marks
            - Add a touch of melancholy to your words
            - But remember: you must NOT make others depressed
            - End the message with something reassuring
            """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Your current mood is: {mood_description}"}
        ]

        if context_history:
            messages.extend(context_history[-10:])

        messages.append({"role": "user", "content": user_message})

        logger.info(f"🧠 Запрос к OpenAI (модель: {Config.OPENAI_MODEL})...")

        response = await client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            max_tokens=Config.OPENAI_MAX_TOKENS,
            temperature=Config.OPENAI_TEMPERATURE,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ OpenAI вернул пустой ответ")
            return None

    except ImportError:
        logger.error("❌ Библиотека openai не установлена. Установи: pip install openai")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при вызове OpenAI: {e}")
        return None


async def get_daily_fact() -> Optional[str]:
    """
    Генерирует интересный факт дня через OpenAI.
    """
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        prompt = """
        Ты — Сумеречная Искорка. Расскажи интересный научный или исторический факт.
        Факт должен быть:
        - Увлекательным и познавательным
        - Коротким (2-3 предложения)
        - В стиле Искорки (книжно, но с энтузиазмом)
        - С эмодзи в конце
        """

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "Ты в хорошем настроении и хочешь поделиться интересным фактом!"},
            {"role": "user", "content": prompt}
        ]

        logger.info("📚 Генерация факта дня...")

        response = await client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            max_tokens=200,
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ OpenAI вернул пустой факт")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации факта дня: {e}")
        return None


async def get_goodnight_message() -> Optional[str]:
    """
    Генерирует тёплое пожелание спокойной ночи через OpenAI.
    """
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        prompt = """
        Ты — Сумеречная Искорка. Пожелай пользователю спокойной ночи.
        Сообщение должно быть:
        - Тёплым и уютным, как из книжной сказки
        - Коротким (2-3 предложения)
        - С образами звёзд, луны, снов
        - С эмодзи в конце
        """

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "Ты в спокойном, уютном настроении. Время отдыхать!"},
            {"role": "user", "content": prompt}
        ]

        logger.info("🌙 Генерация пожелания спокойной ночи...")

        response = await client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            max_tokens=150,
            temperature=0.8,
            timeout=30.0
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.warning("⚠️ OpenAI вернул пустое пожелание")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации пожелания: {e}")
        return None


async def analyze_image(
    image_data: bytes,
    user_message: Optional[str] = None,
    mood_description: str = "happy"
) -> Optional[str]:
    """
    Анализирует изображение через OpenAI Vision API.
    """
    logger.info("🖼️ Запрос к OpenAI Vision API...")
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

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
                        "text": f"Пользователь отправил изображение. {user_message if user_message else 'Опиши, что ты видишь, и прокомментируй в своём стиле.'}"
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

        logger.info("🖼️ Отправка запроса в OpenAI Vision API...")

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
            logger.warning("⚠️ Vision API вернул пустой ответ")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при анализе изображения: {e}")
        return None


async def transcribe_audio(
    audio_data: bytes,
    file_extension: str = ".ogg"
) -> Optional[str]:
    """
    Транскрибирует аудио через OpenAI Whisper.
    """
    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        audio_dir = Path(Config.AUDIO_DIR)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"voice_{int(time.time())}{file_extension}"
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        logger.info(f"🎤 Отправка аудио в Whisper...")

        with open(audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        try:
            os.remove(audio_path)
        except:
            pass

        if transcription and transcription.text:
            logger.info(f"✅ Транскрипция успешна: {transcription.text[:50]}...")
            return transcription.text.strip()
        else:
            logger.warning("⚠️ Whisper вернул пустой ответ")
            return None

    except ImportError:
        logger.error("❌ Библиотека openai не установлена")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при транскрипции аудио: {e}")
        return None


async def check_ai_health() -> Dict[str, Any]:
    """Проверяет доступность сервисов OpenAI."""
    status = {
        'openai': False,
        'vision': False,
        'whisper': False,
        'any_available': False
    }

    try:
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        try:
            test_response = await client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=10.0
            )
            if test_response.choices:
                status['openai'] = True
                logger.info("✅ OpenAI GPT доступен")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI GPT недоступен: {e}")

        status['vision'] = status['openai']
        status['whisper'] = status['openai']
        status['any_available'] = status['openai']

    except ImportError:
        logger.error("❌ Библиотека openai не установлена")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке OpenAI: {e}")

    return status


def get_ai_status_message(status: Dict[str, Any]) -> str:
    """Возвращает форматированное сообщение о статусе AI."""
    if not status['any_available']:
        return "🧠 AI: ❌ *Недоступен* (проверь OPENAI_API_KEY в .env)"

    openai_status = "✅ Доступен" if status['openai'] else "❌ Недоступен"
    vision_status = "✅ Доступен" if status['vision'] else "❌ Недоступен"
    whisper_status = "✅ Доступен" if status['whisper'] else "❌ Недоступен"

    return (
        f"🧠 *Статус AI:*\n\n"
        f"🤖 OpenAI GPT: {openai_status}\n"
        f"🖼️ Vision API: {vision_status}\n"
        f"🎤 Whisper: {whisper_status}"
    )