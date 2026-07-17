"""
Парсер напоминаний для Сумеречной Искорки.
Извлекает дату, время и текст из сообщений пользователя.

Автор: MADAO81
Версия: 1.3 — улучшенная обработка запятых и вежливых слов
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


class ReminderParser:
    """
    Парсит сообщения пользователя и извлекает:
    - дату и время
    - текст напоминания
    - тип повторения (если есть)
    """

    @staticmethod
    def parse_reminder(text: str) -> Optional[Tuple[str, datetime, bool, Optional[str]]]:
        """
        Извлекает из текста напоминание.

        Returns:
            Tuple: (текст_напоминания, datetime, is_recurring, recurring_type)
            или None, если не удалось распарсить
        """
        original_text = text
        text_for_search = text.lower().strip()

        # Проверяем ключевые слова
        if not any(word in text_for_search for word in ["напомни", "напоминание", "напомнить", "запомни"]):
            return None

        # Убираем ключевые слова в начале
        for word in ["напомни", "напоминание", "напомнить", "запомни"]:
            if text_for_search.startswith(word):
                text_for_search = text_for_search[len(word):].strip()
                break

        # Убираем "пожалуйста", "плиз", "пж" и запятые
        text_for_search = text_for_search.replace("пожалуйста", "").strip()
        text_for_search = text_for_search.replace("плиз", "").strip()
        text_for_search = text_for_search.replace("пж", "").strip()
        text_for_search = re.sub(r'[,，、]', ' ', text_for_search).strip()
        text_for_search = re.sub(r'\s+', ' ', text_for_search).strip()

        # Проверяем на повторяющиеся
        is_recurring = False
        recurring_type = None

        if "каждый день" in text_for_search or "ежедневно" in text_for_search:
            is_recurring = True
            recurring_type = "daily"
            text_for_search = text_for_search.replace("каждый день", "").replace("ежедневно", "").strip()
        elif "каждую неделю" in text_for_search or "еженедельно" in text_for_search:
            is_recurring = True
            recurring_type = "weekly"
            text_for_search = text_for_search.replace("каждую неделю", "").replace("еженедельно", "").strip()
        elif "каждый месяц" in text_for_search or "ежемесячно" in text_for_search:
            is_recurring = True
            recurring_type = "monthly"
            text_for_search = text_for_search.replace("каждый месяц", "").replace("ежемесячно", "").strip()

        # --- ПАРСИНГ "ЧЕРЕЗ N ..." ---
        through_match = re.search(r'через\s+(\d+)\s+(дней|день|дня|часов|час|часа|минут|минуты|минуту)', text_for_search)
        if through_match:
            number = int(through_match.group(1))
            unit = through_match.group(2)

            if "день" in unit or "дней" in unit:
                remind_at = datetime.now() + timedelta(days=number)
            elif "час" in unit:
                remind_at = datetime.now() + timedelta(hours=number)
            elif "минут" in unit:
                remind_at = datetime.now() + timedelta(minutes=number)
            else:
                remind_at = datetime.now() + timedelta(days=number)

            text_for_search = re.sub(r'через\s+\d+\s+(дней|день|дня|часов|час|часа|минут|минуты|минуту)', '', text_for_search).strip()

            # Проверяем время
            time_match = re.search(r'в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                remind_at = remind_at.replace(hour=hour, minute=minute, second=0, microsecond=0)
                text_for_search = re.sub(r'в\s+\d{1,2}\s*[:.-]\s*\d{2}', '', text_for_search).strip()

            # Убираем лишние слова
            text_for_search = re.sub(r'^[,，、\s]+', '', text_for_search)
            if not text_for_search:
                text_for_search = "Напоминание"

            return text_for_search, remind_at, is_recurring, recurring_type

        # --- ПАРСИНГ ДАТЫ (НОВЫЙ — ИЩЕМ В ЛЮБОМ МЕСТЕ) ---
        remind_at = None
        matched_text = ""

        # 1. "сегодня в 19-10"
        match = re.search(r'сегодня\s+в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            now = datetime.now()
            remind_at = datetime(now.year, now.month, now.day, hour, minute, 0, 0)
            matched_text = match.group(0)

        # 2. "завтра в 19-10"
        if not remind_at:
            match = re.search(r'завтра\s+в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                now = datetime.now() + timedelta(days=1)
                remind_at = datetime(now.year, now.month, now.day, hour, minute, 0, 0)
                matched_text = match.group(0)

        # 3. "17 июля в 19-10"
        if not remind_at:
            match = re.search(r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                day = int(match.group(1))
                month = ReminderParser._month_to_number(match.group(2))
                hour = int(match.group(3))
                minute = int(match.group(4))
                year = datetime.now().year
                remind_at = datetime(year, month, day, hour, minute, 0, 0)
                matched_text = match.group(0)

        # 4. "17-07-2026 в 19-10"
        if not remind_at:
            match = re.search(r'(\d{1,2})[-./](\d{1,2})[-./](\d{4})\s+в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                hour = int(match.group(4))
                minute = int(match.group(5))
                remind_at = datetime(year, month, day, hour, minute, 0, 0)
                matched_text = match.group(0)

        # 5. "17.07 в 19-10"
        if not remind_at:
            match = re.search(r'(\d{1,2})[-./](\d{1,2})\s+в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                hour = int(match.group(3))
                minute = int(match.group(4))
                year = datetime.now().year
                remind_at = datetime(year, month, day, hour, minute, 0, 0)
                matched_text = match.group(0)

        # 6. Просто "в 19-10" (сегодня)
        if not remind_at:
            match = re.search(r'в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                now = datetime.now()
                remind_at = datetime(now.year, now.month, now.day, hour, minute, 0, 0)
                matched_text = match.group(0)

        if remind_at is None:
            return None

        # Убираем дату и время из текста
        if matched_text:
            text_for_search = text_for_search.replace(matched_text, "").strip()

        # Убираем лишние слова и запятые
        text_for_search = re.sub(r'^[,，、\s]+', '', text_for_search)

        if not text_for_search:
            text_for_search = "Напоминание"

        return text_for_search, remind_at, is_recurring, recurring_type

    @staticmethod
    def _month_to_number(month_name: str) -> int:
        """Переводит название месяца в число."""
        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }
        return months.get(month_name.lower(), 1)
