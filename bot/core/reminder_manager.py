"""
Менеджер напоминаний для Сумеречной Искорки.
Поддерживает личные и групповые напоминания.

Автор: MADAO81
Версия: 2.3 — умный поиск с нормализацией текста
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bot.config import Config


class ReminderManager:
    def __init__(self):
        self.db_path = Config.REMINDERS_DB
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                is_recurring BOOLEAN DEFAULT 0,
                recurring_type TEXT DEFAULT NULL,
                is_private BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_remind_at ON reminders (remind_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON reminders (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON reminders (is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_private ON reminders (is_private)")
        conn.commit()
        conn.close()

    def add_reminder(self, user_id: int, chat_id: int, text: str, remind_at: datetime,
                     is_recurring: bool = False, recurring_type: Optional[str] = None,
                     is_private: bool = False) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (user_id, chat_id, text, remind_at, is_recurring, recurring_type, is_private)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, chat_id, text, remind_at, is_recurring, recurring_type, is_private))
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id

    def get_due_reminders(self) -> List[Dict]:
        now = datetime.now()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, chat_id, text, remind_at, is_recurring, recurring_type, is_private
            FROM reminders
            WHERE remind_at <= ? AND is_active = 1
        """, (now,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def mark_sent(self, reminder_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def reschedule_recurring(self, reminder_id: int, recurring_type: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT remind_at FROM reminders WHERE id = ?", (reminder_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        current_time = datetime.fromisoformat(row[0])
        if recurring_type == "daily":
            next_time = current_time + timedelta(days=1)
        elif recurring_type == "weekly":
            next_time = current_time + timedelta(days=7)
        elif recurring_type == "monthly":
            next_time = current_time + timedelta(days=30)
        else:
            conn.close()
            return False
        cursor.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", (next_time, reminder_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_user_reminders(self, user_id: int, chat_id: Optional[int] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if chat_id:
            cursor.execute("""
                SELECT id, text, remind_at, is_recurring, recurring_type, is_private, chat_id
                FROM reminders
                WHERE is_active = 1
                AND (
                    (is_private = 1 AND user_id = ?)
                    OR (is_private = 0 AND chat_id = ?)
                )
                ORDER BY remind_at ASC
            """, (user_id, chat_id))
        else:
            cursor.execute("""
                SELECT id, text, remind_at, is_recurring, recurring_type, is_private
                FROM reminders
                WHERE is_active = 1 AND is_private = 1 AND user_id = ?
                ORDER BY remind_at ASC
            """, (user_id,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def _normalize(self, text: str) -> str:
        """Нормализует текст для поиска: убирает мягкий знак, приводит к нижнему регистру."""
        text = text.lower()
        # Убираем мягкий знак
        text = text.replace("ь", "")
        # Убираем @упоминания
        text = text.replace("@twilightsparklerusbot", "").replace("@twilight_sparkle_rus_bot", "")
        # Убираем лишние пробелы
        text = " ".join(text.split())
        return text

    def cancel_reminder_by_text(self, user_id: int, text_contains: str, chat_id: Optional[int] = None) -> bool:
        """Отменяет напоминание по части текста (умный поиск с нормализацией)."""
        clean_query = self._normalize(text_contains)
        keywords = [w for w in clean_query.split() if len(w) > 2]

        if not keywords:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Получаем все активные напоминания пользователя
        if chat_id:
            cursor.execute("""
                SELECT id, text FROM reminders
                WHERE user_id = ? 
                AND is_active = 1
                AND (
                    (is_private = 1 AND user_id = ?)
                    OR (is_private = 0 AND chat_id = ?)
                )
            """, (user_id, user_id, chat_id))
        else:
            cursor.execute("""
                SELECT id, text FROM reminders
                WHERE user_id = ? 
                AND is_active = 1
                AND is_private = 1
            """, (user_id,))

        rows = cursor.fetchall()
        if not rows:
            conn.close()
            return False

        # Ищем совпадения по нормализованному тексту
        found_ids = []
        for reminder_id, text in rows:
            normalized_text = self._normalize(text)
            # Проверяем, содержит ли нормализованный текст все ключевые слова
            if all(kw in normalized_text for kw in keywords):
                found_ids.append(reminder_id)

        if not found_ids:
            conn.close()
            return False

        # Удаляем все найденные
        placeholders = ", ".join(["?" for _ in found_ids])
        cursor.execute(f"UPDATE reminders SET is_active = 0 WHERE id IN ({placeholders})", found_ids)

        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
