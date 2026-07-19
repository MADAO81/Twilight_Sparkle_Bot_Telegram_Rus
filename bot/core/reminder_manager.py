"""
Менеджер напоминаний для Сумеречной Искорки.
Поддерживает личные и групповые напоминания.

Автор: MADAO81
Версия: 2.0 — разделение на личные и групповые
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
        """Добавляет напоминание."""
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
        """Получает все активные напоминания, время которых наступило."""
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
        """Отмечает напоминание как отправленное."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def reschedule_recurring(self, reminder_id: int, recurring_type: str) -> bool:
        """Переносит повторяющееся напоминание."""
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
        """
        Получает напоминания пользователя.
        - Личные: только для этого пользователя
        - Групповые: для всех участников группы
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if chat_id:
            # Для группы: личные пользователя + все групповые
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
            # Для лички: только личные
            cursor.execute("""
                SELECT id, text, remind_at, is_recurring, recurring_type, is_private
                FROM reminders
                WHERE is_active = 1 AND is_private = 1 AND user_id = ?
                ORDER BY remind_at ASC
            """, (user_id,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def cancel_reminder_by_text(self, user_id: int, text_contains: str, chat_id: Optional[int] = None) -> bool:
        """Отменяет напоминание по части текста."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if chat_id:
            cursor.execute("""
                UPDATE reminders SET is_active = 0
                WHERE user_id = ? AND text LIKE ? AND is_active = 1
                AND (
                    (is_private = 1 AND user_id = ?)
                    OR (is_private = 0 AND chat_id = ?)
                )
                LIMIT 1
            """, (user_id, f"%{text_contains}%", user_id, chat_id))
        else:
            cursor.execute("""
                UPDATE reminders SET is_active = 0
                WHERE user_id = ? AND text LIKE ? AND is_active = 1 AND is_private = 1
                LIMIT 1
            """, (user_id, f"%{text_contains}%"))

        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
