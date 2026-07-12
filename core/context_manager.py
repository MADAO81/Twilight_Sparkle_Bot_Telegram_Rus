# bot/core/context_manager.py
"""
Менеджер контекста диалогов.
Хранение истории общения в SQLite (30 дней).

Автор: MADAO81
Версия: 1.0
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bot.config import Config


class ContextManager:
    """
    Класс для управления историей диалогов.
    Хранит сообщения пользователей и ответы бота в SQLite.
    """

    def __init__(self):
        """Инициализация менеджера контекста."""
        self.db_path = Config.CONVERSATIONS_DB
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON conversations (user_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON conversations (timestamp)
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")

    def get_context(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            expire_date = datetime.now() - timedelta(days=Config.CONTEXT_EXPIRE_DAYS)
            cursor.execute(
                "DELETE FROM conversations WHERE timestamp < ?",
                (expire_date,)
            )
            conn.commit()

            cursor.execute("""
                SELECT role, content FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))

            rows = cursor.fetchall()
            conn.close()

            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

        except Exception as e:
            print(f"Ошибка при получении контекста: {e}")
            return []

    def save_context(self, user_id: int, user_message: str, bot_response: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO conversations (user_id, role, content)
                VALUES (?, ?, ?)
            """, (user_id, "user", user_message))

            cursor.execute("""
                INSERT INTO conversations (user_id, role, content)
                VALUES (?, ?, ?)
            """, (user_id, "assistant", bot_response))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Ошибка при сохранении контекста: {e}")

    def clear_context(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM conversations WHERE user_id = ?",
                (user_id,)
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Ошибка при очистке контекста: {e}")