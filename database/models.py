from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """Модель задачи"""
    id: int
    user_id: int
    text: str
    category: str  # 'reminder', 'task', 'event'
    event_at: Optional[datetime]
    remind_at: Optional[datetime]
    reminder_offset_minutes: Optional[int]
    completed: bool
    notified: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row: tuple) -> 'Task':
        """Создать Task из строки БД"""
        # Support both old and new schemas (columns order may differ depending on DB migration)
        # Old schema rows length: 9 (id, user_id, text, category, remind_at, completed, notified, created_at, updated_at)
        # New schema rows length: 11 (id, user_id, text, category, event_at, remind_at, reminder_offset_minutes, completed, notified, created_at, updated_at)
        if len(row) == 9:
            # legacy layout
            return cls(
                id=row[0],
                user_id=row[1],
                text=row[2],
                category=row[3] or 'reminder',
                event_at=datetime.fromisoformat(row[4]) if row[4] else None,
                remind_at=datetime.fromisoformat(row[4]) if row[4] else None,
                reminder_offset_minutes=None,
                completed=bool(row[5]),
                notified=bool(row[6]),
                created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
            )

        # For rows with new schema or with appended columns, try to map by expected positions and fallback gracefully
        # Prefer to read known positions if available
        def safe_iso(val):
            return datetime.fromisoformat(val) if val else None

        # Try to detect event_at position: if len >= 11 assume new schema
        if len(row) >= 11:
            return cls(
                id=row[0],
                user_id=row[1],
                text=row[2],
                category=row[3] or 'reminder',
                event_at=safe_iso(row[4]),
                remind_at=safe_iso(row[5]),
                reminder_offset_minutes=int(row[6]) if row[6] is not None else None,
                completed=bool(row[7]),
                notified=bool(row[8]),
                created_at=safe_iso(row[9]) or datetime.now(),
                updated_at=safe_iso(row[10]) or datetime.now()
            )

        # Fallback: try to find timestamp-like fields by content (best-effort)
        # We'll attempt a tolerant mapping using known column types positions
        try:
            # attempt to parse by names/heuristics
            # assume: id, user_id, text, category, remind_at, completed, notified, created_at, updated_at, [maybe event_at, reminder_offset_minutes]
            return cls(
                id=row[0],
                user_id=row[1],
                text=row[2],
                category=row[3] or 'reminder',
                event_at=safe_iso(row[4]) if isinstance(row[4], str) and 'T' in row[4] else None,
                remind_at=safe_iso(row[4]) if isinstance(row[4], str) and 'T' in row[4] else None,
                reminder_offset_minutes=None,
                completed=bool(row[5]),
                notified=bool(row[6]),
                created_at=safe_iso(row[7]) or datetime.now(),
                updated_at=safe_iso(row[8]) or datetime.now()
            )
        except Exception:
            # last resort: create minimal object
            return cls(
                id=row[0],
                user_id=row[1],
                text=row[2],
                category='reminder',
                event_at=None,
                remind_at=None,
                reminder_offset_minutes=None,
                completed=False,
                notified=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'text': self.text,
            'category': self.category,
            'event_at': self.event_at.isoformat() if self.event_at else None,
            'remind_at': self.remind_at.isoformat() if self.remind_at else None,
            'reminder_offset_minutes': self.reminder_offset_minutes,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
