# bot/scripts/create_books_db.py
"""
Скрипт для создания базы данных книг (fallback для /book).

Автор: MADAO81
Версия: 1.0
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "books.db"


def init_db():
    """Создаёт таблицу книг."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            description TEXT NOT NULL,
            genre TEXT DEFAULT 'приключения',
            source TEXT DEFAULT 'книга'
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_genre 
        ON books (genre)
    """)

    conn.commit()
    conn.close()
    print(f"✅ База данных книг создана: {DB_PATH}")


if __name__ == "__main__":
    init_db()