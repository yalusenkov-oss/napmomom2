from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    """Схема создания задачи"""
    text: str = Field(..., min_length=1, max_length=500, description="Текст задачи")
    category: str = Field(default="reminder", description="Категория: reminder, task, event")
    # event_at - время самого события (в приложении отображается как время события)
    event_at: Optional[datetime] = Field(default=None, description="Время события")
    # Дополнительный отступ (в минутах) — например "за 15 минут". None означает "Не указано" (автоматический выбор)
    reminder_offset_minutes: Optional[int] = Field(default=None, description="Дополнительное напоминание в минутах")
    # remind_at оставляем на уровне совместимости — фактическое время отправки может быть рассчитано сервером
    remind_at: Optional[datetime] = Field(default=None, description="Когда напомнить (приоритетно для ручной установки)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Позвонить маме",
                "category": "reminder",
                "remind_at": "2024-12-20T15:00:00"
            }
        }


class TaskUpdate(BaseModel):
    """Схема обновления задачи"""
    text: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = None
    event_at: Optional[datetime] = None
    reminder_offset_minutes: Optional[int] = None
    remind_at: Optional[datetime] = None
    completed: Optional[bool] = None


class TaskToggle(BaseModel):
    """Схема переключения статуса"""
    task_id: int


class TaskResponse(BaseModel):
    """Схема ответа с задачей"""
    id: int
    text: str
    category: str
    event_at: Optional[str] = None
    remind_at: Optional[str] = None
    reminder_offset_minutes: Optional[int] = None
    completed: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Схема списка задач"""
    tasks: List[TaskResponse]
    counts: Optional[dict] = None


class CountsResponse(BaseModel):
    """Схема счётчиков"""
    all: int
    today: int
    active: int
    completed: int


class MessageResponse(BaseModel):
    """Простой ответ с сообщением"""
    status: str
    message: Optional[str] = None
    id: Optional[int] = None
