# bot/scripts/create_reminders_db.py
"""
Скрипт для создания базы данных напоминаний.

Автор: MADAO81
Версия: 1.0
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "reminders.db"


def init_db():
    """Создаёт таблицу напоминаний."""
    conn = sqlite3.connect(DB_PATH)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_remind_at 
        ON reminders (remind_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_id 
        ON reminders (user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_is_active 
        ON reminders (is_active)
    """)

    conn.commit()
    conn.close()
    print(f"✅ База данных напоминаний создана: {DB_PATH}")


if __name__ == "__main__":
    init_db()