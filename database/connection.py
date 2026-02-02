import aiosqlite
import sqlite3
from pathlib import Path
from typing import Optional

# Путь к файлу базы данных
DB_PATH = Path(__file__).parent.parent / "data" / "taskbot.db"

# Один общий асинхронный коннекшн для приложения.
# Используем единый объект, чтобы избежать повторного старта фоновых потоков
# внутри aiosqlite при многократных подключениях / перезапусках кода.
_DB_CONN: Optional[aiosqlite.Connection] = None


async def init_db_connection():
    """Инициализировать и сохранить глобальное асинхронное подключение.

    Вызывать один раз при старте приложения (после создания файла/таблиц).
    """
    global _DB_CONN
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _DB_CONN is None:
        _DB_CONN = await aiosqlite.connect(DB_PATH)
    return _DB_CONN


async def get_db():
    """Получить асинхронное подключение к базе данных (единственный экземпляр).

    Если соединение ещё не инициализировано — создаётся новый.
    Возвращаем объект подключения (не контекстный менеджер).
    """
    global _DB_CONN
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _DB_CONN is None:
        _DB_CONN = await aiosqlite.connect(DB_PATH)
    return _DB_CONN


async def init_db():
    """Инициализация базы данных — создание таблиц.

    Для инициализации используем синхронный sqlite3, чтобы избежать проблем
    с запуском фоновых потоков в aiosqlite при старте приложения (uvicorn --reload).
    После инициализации обычные операции в коде могут использовать aiosqlite через get_db().
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Используем синхронный sqlite3 для создания таблиц (без фоновых потоков)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                category TEXT DEFAULT 'reminder',
                event_at TIMESTAMP,
                remind_at TIMESTAMP,
                reminder_offset_minutes INTEGER,
                completed BOOLEAN DEFAULT FALSE,
                notified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_tasks_user_id 
            ON tasks(user_id)
        ''')

        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_tasks_remind 
            ON tasks(remind_at, completed, notified)
        ''')

        conn.commit()
        print("✅ База данных инициализирована")
    finally:
        conn.close()

    # Попробуем мягко добавить новые колонки в существующую базу (если обновляем старую схему)
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Проверяем наличие столбца event_at
        cur.execute("PRAGMA table_info(tasks)")
        cols = [r[1] for r in cur.fetchall()]
        if 'event_at' not in cols:
            try:
                cur.execute('ALTER TABLE tasks ADD COLUMN event_at TIMESTAMP')
            except Exception:
                pass
        if 'reminder_offset_minutes' not in cols:
            try:
                cur.execute('ALTER TABLE tasks ADD COLUMN reminder_offset_minutes INTEGER')
            except Exception:
                pass
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def close_db_connection():
    """Закрыть глобальное асинхронное подключение, если оно открыто."""
    global _DB_CONN
    if _DB_CONN is not None:
        try:
            await _DB_CONN.close()
        finally:
            _DB_CONN = None
