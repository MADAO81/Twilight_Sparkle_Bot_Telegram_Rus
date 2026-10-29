"""
Парсер напоминаний для Сумеречной Искорки.
Поддерживает личные и групповые, а также ежемесячные повторения.

Автор: MADAO81
Версия: 3.2 — убираем одиночный @ и вырезаем ключевые слова в любом месте
"""

import re
import calendar
from datetime import datetime, timedelta
from typing import Optional, Tuple


class ReminderParser:
    @staticmethod
    def parse_reminder(text: str) -> Optional[Tuple[str, datetime, bool, Optional[str], bool]]:
        """
        Извлекает из текста напоминание.

        Returns:
            Tuple: (текст, datetime, is_recurring, recurring_type, is_private)
            или None, если не удалось распарсить
        """
        text_for_search = text.lower().strip()

        # === УБИРАЕМ @УПОМИНАНИЯ (с словом и одиночные) ===
        text_for_search = re.sub(r'@\w+', '', text_for_search)   # @username
        text_for_search = re.sub(r'@\s*', '', text_for_search)    # одиночный @
        text_for_search = re.sub(r'\s+', ' ', text_for_search).strip()

        # Проверяем ключевые слова
        has_reminder_keyword = any(
            word in text_for_search
            for word in ["напомни", "напоминай", "напоминание", "напомнить", "запомни"]
        )
        has_group_keyword = "групповое" in text_for_search

        if not has_reminder_keyword and not has_group_keyword:
            return None

        # Если есть "групповое", но нет "напомни" — добавляем "напомни" для парсера
        if has_group_keyword and not has_reminder_keyword:
            text_for_search = "напомни " + text_for_search

        # === ВЫРЕЗАЕМ КЛЮЧЕВЫЕ СЛОВА В ЛЮБОМ МЕСТЕ (не только startswith) ===
        # Сначала длинные формы, потом короткие
        for word in ["напоминай мне", "напоминай", "напоминание", "напомнить", "напомни", "запомни"]:
            if word in text_for_search:
                text_for_search = text_for_search.replace(word, "", 1).strip()

        text_for_search = re.sub(r'\s+', ' ', text_for_search).strip()

        # Определяем тип: личное или групповое (по умолчанию — личное)
        is_private = True
        if "групповое" in text_for_search or "в группу" in text_for_search or "для всех" in text_for_search:
            is_private = False
            text_for_search = text_for_search.replace("групповое", "").replace("в группу", "").replace("для всех", "").strip()
        elif "личное" in text_for_search or "в личку" in text_for_search or "только мне" in text_for_search:
            is_private = True
            text_for_search = text_for_search.replace("личное", "").replace("в личку", "").replace("только мне", "").strip()

        # Убираем вежливые слова и запятые
        text_for_search = text_for_search.replace("пожалуйста", "").strip()
        text_for_search = text_for_search.replace("плиз", "").strip()
        text_for_search = text_for_search.replace("пж", "").strip()
        text_for_search = re.sub(r'[,，、]', ' ', text_for_search).strip()
        text_for_search = re.sub(r'\s+', ' ', text_for_search).strip()

        # ============================================================
        # ВАЖНО: парсим "20-го числа каждого месяца" ДО вырезания "каждый месяц"
        # ============================================================
        is_recurring = False
        recurring_type = None
        recurring_day = None

        monthly_match = re.search(
            r'(\d{1,2})[-]?го?\s+числа\s+(каждого\s+месяца|каждый\s+месяц)',
            text_for_search
        )
        if monthly_match:
            recurring_day = int(monthly_match.group(1))
            is_recurring = True
            recurring_type = "monthly"
            text_for_search = text_for_search.replace(monthly_match.group(0), "").strip()

        if not monthly_match:
            monthly_match_rev = re.search(
                r'(каждого\s+месяца|каждый\s+месяц)\s+(\d{1,2})[-]?го?\s+числа',
                text_for_search
            )
            if monthly_match_rev:
                recurring_day = int(monthly_match_rev.group(2))
                is_recurring = True
                recurring_type = "monthly"
                text_for_search = text_for_search.replace(monthly_match_rev.group(0), "").strip()

        if not is_recurring:
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

        # --- ПАРСИНГ ДАТЫ ---
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

        # 4. "20-го числа в 10-15" (без месяца)
        if not remind_at:
            match = re.search(r'(\d{1,2})[-]?го?\s+числа\s+в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                day = int(match.group(1))
                hour = int(match.group(2))
                minute = int(match.group(3))
                now = datetime.now()

                if is_recurring and recurring_type == "monthly":
                    if day < now.day or (day == now.day and (hour < now.hour or (hour == now.hour and minute <= now.minute))):
                        if now.month == 12:
                            month = 1
                            year = now.year + 1
                        else:
                            month = now.month + 1
                            year = now.year
                    else:
                        month = now.month
                        year = now.year
                    remind_at = datetime(year, month, day, hour, minute, 0, 0)
                else:
                    if day < now.day:
                        if now.month == 12:
                            month = 1
                            year = now.year + 1
                        else:
                            month = now.month + 1
                            year = now.year
                    else:
                        month = now.month
                        year = now.year
                    remind_at = datetime(year, month, day, hour, minute, 0, 0)

                matched_text = match.group(0)

        # 5. "17-07-2026 в 19-10"
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

        # 6. "17.07 в 19-10"
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

        # 7. Просто "в 19-10"
        if not remind_at:
            match = re.search(r'в\s+(\d{1,2})\s*[:.-]\s*(\d{2})', text_for_search)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                now = datetime.now()

                if is_recurring and recurring_type == "monthly" and recurring_day:
                    if recurring_day < now.day or (
                        recurring_day == now.day
                        and (hour < now.hour or (hour == now.hour and minute <= now.minute))
                    ):
                        if now.month == 12:
                            month = 1
                            year = now.year + 1
                        else:
                            month = now.month + 1
                            year = now.year
                    else:
                        month = now.month
                        year = now.year
                    remind_at = datetime(year, month, recurring_day, hour, minute, 0, 0)
                else:
                    remind_at = datetime(now.year, now.month, now.day, hour, minute, 0, 0)

                matched_text = match.group(0)

        if remind_at is None:
            return None

        if recurring_type == "monthly" and recurring_day:
            try:
                remind_at = remind_at.replace(day=recurring_day)
            except ValueError:
                last_day = calendar.monthrange(remind_at.year, remind_at.month)[1]
                remind_at = remind_at.replace(day=min(recurring_day, last_day))

        if matched_text:
            text_for_search = text_for_search.replace(matched_text, "").strip()

        text_for_search = re.sub(r'^[,，、\s]+', '', text_for_search)
        text_for_search = re.sub(r'\s+', ' ', text_for_search).strip()

        if not text_for_search:
            text_for_search = "Напоминание"

        return text_for_search, remind_at, is_recurring, recurring_type, is_private

    @staticmethod
    def _month_to_number(month_name: str) -> int:
        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
        }
        return months.get(month_name.lower(), 1)
