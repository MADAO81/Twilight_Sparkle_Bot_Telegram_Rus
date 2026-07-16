# bot/core/reminder_parser.py
"""
Парсер напоминаний для Сумеречной Искорки.
Извлекает дату, время и текст из сообщений пользователя.

Автор: MADAO81
Версия: 1.0
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
        text = text.lower().strip()

        # Проверяем ключевые слова
        if not any(word in text for word in ["напомни", "напоминание", "напомнить", "запомни"]):
            return None

        # Убираем ключевые слова в начале
        for word in ["напомни", "напоминание", "напомнить", "запомни"]:
            if text.startswith(word):
                text = text[len(word):].strip()
                break

        # Проверяем на повторяющиеся
        is_recurring = False
        recurring_type = None

        if "каждый день" in text or "ежедневно" in text or "каждый день" in text:
            is_recurring = True
            recurring_type = "daily"
            text = text.replace("каждый день", "").replace("ежедневно", "").strip()
        elif "каждую неделю" in text or "еженедельно" in text:
            is_recurring = True
            recurring_type = "weekly"
            text = text.replace("каждую неделю", "").replace("еженедельно", "").strip()
        elif "каждый месяц" in text or "ежемесячно" in text:
            is_recurring = True
            recurring_type = "monthly"
            text = text.replace("каждый месяц", "").replace("ежемесячно", "").strip()

        # Парсим "через N дней/часов/минут"
        through_match = re.search(r'через\s+(\d+)\s+(дней|день|дня|часов|час|часа|минут|минуты|минуту)', text)
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

            # Убираем часть с "через ..." из текста
            text = re.sub(r'через\s+\d+\s+(дней|день|дня|часов|час|часа|минут|минуты|минуту)', '', text).strip()

            # Проверяем, есть ли указание времени
            time_match = re.search(r'в\s+(\d{1,2})[:.](\d{2})', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                remind_at = remind_at.replace(hour=hour, minute=minute, second=0, microsecond=0)
                text = re.sub(r'в\s+\d{1,2}[:.]\d{2}', '', text).strip()

            return text, remind_at, is_recurring, recurring_type

        # Парсим "15 июля в 14:00"
        date_patterns = [
            # 15 июля в 14:00
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+в\s+(\d{1,2})[:.](\d{2})',
            # 15.07 в 14:00
            r'(\d{1,2})[./](\d{1,2})\s+в\s+(\d{1,2})[:.](\d{2})',
            # сегодня в 14:00
            r'сегодня\s+в\s+(\d{1,2})[:.](\d{2})',
            # завтра в 14:00
            r'завтра\s+в\s+(\d{1,2})[:.](\d{2})',
        ]

        remind_at = None
        matched_text = ""

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()

                if "января" in pattern:
                    day = int(groups[0])
                    month = ReminderParser._month_to_number(groups[1])
                    hour = int(groups[2])
                    minute = int(groups[3])
                    year = datetime.now().year
                    remind_at = datetime(year, month, day, hour, minute, 0, 0)
                    matched_text = match.group(0)

                elif "сегодня" in pattern:
                    hour = int(groups[0])
                    minute = int(groups[1])
                    now = datetime.now()
                    remind_at = datetime(now.year, now.month, now.day, hour, minute, 0, 0)
                    matched_text = match.group(0)

                elif "завтра" in pattern:
                    hour = int(groups[0])
                    minute = int(groups[1])
                    now = datetime.now() + timedelta(days=1)
                    remind_at = datetime(now.year, now.month, now.day, hour, minute, 0, 0)
                    matched_text = match.group(0)

                else:  # 15.07 в 14:00
                    day = int(groups[0])
                    month = int(groups[1])
                    hour = int(groups[2])
                    minute = int(groups[3])
                    year = datetime.now().year
                    remind_at = datetime(year, month, day, hour, minute, 0, 0)
                    matched_text = match.group(0)

                break

        if remind_at is None:
            return None

        # Убираем дату и время из текста
        text = text.replace(matched_text, "").strip()

        # Если текст пустой, ставим дефолтный
        if not text:
            text = "Напоминание"

        return text, remind_at, is_recurring, recurring_type

    @staticmethod
    def _month_to_number(month_name: str) -> int:
        """Переводит название месяца в число."""
        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }
        return months.get(month_name.lower(), 1)