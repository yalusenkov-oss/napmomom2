from datetime import datetime, timedelta
from typing import Optional, List
from database.connection import get_db
from database.models import Task


class TaskRepository:
    """Репозиторий для работы с задачами"""
    
    @staticmethod
    async def create(
        user_id: int,
        text: str,
        category: str = 'reminder',
        event_at: Optional[datetime] = None,
        reminder_offset_minutes: Optional[int] = None,
        remind_at: Optional[datetime] = None
    ) -> int:
        """Создать новую задачу"""
        db = await get_db()
        # если remind_at не передан, вычислим его из event_at и reminder_offset_minutes
        computed_remind = remind_at
        if computed_remind is None and event_at is not None:
            if reminder_offset_minutes is not None:
                computed_remind = event_at - timedelta(minutes=reminder_offset_minutes)
            else:
                computed_remind = event_at

        cursor = await db.execute(
            '''
            INSERT INTO tasks (user_id, text, category, event_at, remind_at, reminder_offset_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                text,
                category,
                event_at.isoformat() if event_at else None,
                computed_remind.isoformat() if computed_remind else None,
                reminder_offset_minutes
            )
        )
        await db.commit()
        return cursor.lastrowid
    
    @staticmethod
    async def get_by_id(task_id: int, user_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        db = await get_db()
        cursor = await db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
            (task_id, user_id)
        )
        row = await cursor.fetchone()
        return Task.from_row(row) if row else None
    
    @staticmethod
    async def get_all_by_user(user_id: int) -> List[Task]:
        """Получить все задачи пользователя"""
        db = await get_db()
        cursor = await db.execute(
            '''
            SELECT * FROM tasks 
            WHERE user_id = ? 
            ORDER BY completed, remind_at
            ''',
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def get_today(user_id: int) -> List[Task]:
        """Получить задачи на сегодня"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        
        db = await get_db()
        cursor = await db.execute(
            '''
            SELECT * FROM tasks 
            WHERE user_id = ? 
            AND remind_at BETWEEN ? AND ?
            ORDER BY remind_at
            ''',
            (user_id, today_start.isoformat(), today_end.isoformat())
        )
        rows = await cursor.fetchall()
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def get_active(user_id: int) -> List[Task]:
        """Получить активные (невыполненные) задачи"""
        db = await get_db()
        cursor = await db.execute(
            '''
            SELECT * FROM tasks 
            WHERE user_id = ? AND completed = FALSE
            ORDER BY remind_at
            ''',
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def get_completed(user_id: int) -> List[Task]:
        """Получить выполненные задачи"""
        db = await get_db()
        cursor = await db.execute(
            '''
            SELECT * FROM tasks 
            WHERE user_id = ? AND completed = TRUE
            ORDER BY updated_at DESC
            ''',
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def get_pending_reminders() -> List[Task]:
        """Получить задачи, которые нужно напомнить"""
        now = datetime.now().isoformat()
        
        db = await get_db()
        cursor = await db.execute(
            '''
            SELECT * FROM tasks 
            WHERE remind_at <= ? 
            AND completed = FALSE 
            AND notified = FALSE
            ''',
            (now,)
        )
        rows = await cursor.fetchall()
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    async def update(
        task_id: int,
        user_id: int,
        text: Optional[str] = None,
        category: Optional[str] = None,
        event_at: Optional[datetime] = None,
        reminder_offset_minutes: Optional[int] = None,
        remind_at: Optional[datetime] = None,
        completed: Optional[bool] = None
    ) -> bool:
        """Обновить задачу"""
        # Собираем поля для обновления
        updates = []
        values = []
        
        if text is not None:
            updates.append('text = ?')
            values.append(text)
        
        if category is not None:
            updates.append('category = ?')
            values.append(category)
        
        if event_at is not None:
            updates.append('event_at = ?')
            values.append(event_at.isoformat())

        if reminder_offset_minutes is not None:
            updates.append('reminder_offset_minutes = ?')
            values.append(reminder_offset_minutes)

        if remind_at is not None:
            updates.append('remind_at = ?')
            values.append(remind_at.isoformat())
        
        if completed is not None:
            updates.append('completed = ?')
            values.append(completed)
        
        if not updates:
            return False
        
        updates.append('updated_at = ?')
        values.append(datetime.now().isoformat())
        
        values.extend([task_id, user_id])
        
        db = await get_db()
        cursor = await db.execute(
            f'''
            UPDATE tasks 
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
            ''',
            values
        )
        await db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    async def toggle_completed(task_id: int, user_id: int) -> bool:
        """Переключить статус выполнения"""
        db = await get_db()
        cursor = await db.execute(
            '''
            UPDATE tasks 
            SET completed = NOT completed, updated_at = ?
            WHERE id = ? AND user_id = ?
            ''',
            (datetime.now().isoformat(), task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    async def mark_notified(task_id: int) -> bool:
        """Отметить задачу как отправленную (напоминание отправлено)"""
        db = await get_db()
        cursor = await db.execute(
            'UPDATE tasks SET notified = TRUE WHERE id = ?',
            (task_id,)
        )
        await db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    async def delete(task_id: int, user_id: int) -> bool:
        """Удалить задачу"""
        db = await get_db()
        cursor = await db.execute(
            'DELETE FROM tasks WHERE id = ? AND user_id = ?',
            (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    async def get_counts(user_id: int) -> dict:
        """Получить количество задач по категории фильтров"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        
        db = await get_db()
        # Всего
        cursor = await db.execute(
            'SELECT COUNT(*) FROM tasks WHERE user_id = ?',
            (user_id,)
        )
        total = (await cursor.fetchone())[0]

        # Сегодня
        cursor = await db.execute(
            '''
            SELECT COUNT(*) FROM tasks 
            WHERE user_id = ? AND remind_at BETWEEN ? AND ?
            ''',
            (user_id, today_start.isoformat(), today_end.isoformat())
        )
        today = (await cursor.fetchone())[0]

        # Активные
        cursor = await db.execute(
            'SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = FALSE',
            (user_id,)
        )
        active = (await cursor.fetchone())[0]

        # Выполненные
        cursor = await db.execute(
            'SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = TRUE',
            (user_id,)
        )
        completed = (await cursor.fetchone())[0]

        return {
            'all': total,
            'today': today,
            'active': active,
            'completed': completed
        }
