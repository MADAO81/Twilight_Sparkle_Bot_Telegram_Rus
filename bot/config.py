"""
Конфигурация бота Сумеречная Искорка.
Загрузка переменных окружения из .env файла.

Автор: MADAO81
Версия: 2.0 — DeepSeek + ProxyAPI + веб-поиск
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    """Класс конфигурации бота."""

    # ========== TELEGRAM ==========
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # ========== PROXYAPI (универсальный) ==========
    PROXY_API_KEY = os.getenv("PROXY_API_KEY")

    # ========== DEEPSEEK (текст + поиск) ==========
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-v4-flash")
    DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", 2000))
    DEEPSEEK_TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", 0.9))

    # ========== OPENAI (картинки + голос) ==========
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", 1000))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.85))

    # ========== КООРДИНАТЫ ==========
    DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", 55.0965))
    DEFAULT_LON = float(os.getenv("DEFAULT_LON", 36.6355))

    # ========== РАБОЧЕЕ ВРЕМЯ ==========
    WORK_START_HOUR = int(os.getenv("WORK_START_HOUR", 9))
    WORK_END_HOUR = int(os.getenv("WORK_END_HOUR", 22))
    CONTEXT_EXPIRE_DAYS = int(os.getenv("CONTEXT_EXPIRE_DAYS", 30))

    # ========== АДМИНИСТРАТОР ==========
    ADMIN_ID = os.getenv("ADMIN_ID")

    # ========== РЕЖИМ ОТЛАДКИ ==========
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

    # ========== ПУТИ ==========
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    AUDIO_DIR = DATA_DIR / "audio"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # ========== БАЗЫ ДАННЫХ ==========
    CONVERSATIONS_DB = DATA_DIR / "conversations.db"
    REMINDERS_DB = DATA_DIR / "reminders.db"
    BOOKS_DB = DATA_DIR / "books.db"
