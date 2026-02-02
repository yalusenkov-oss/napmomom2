from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime

from api.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskToggle,
    CountsResponse
)
from api.schemas.task import MessageResponse
from api.middleware import get_user_id
from database import TaskRepository

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    filter: Optional[str] = None,
    user_id: int = Depends(get_user_id)
):
    """
    Получить список задач
    
    Параметры:
    - filter: all, today, active, completed
    """
    # Получаем задачи в зависимости от фильтра
    if filter == "today":
        tasks = await TaskRepository.get_today(user_id)
    elif filter == "active":
        tasks = await TaskRepository.get_active(user_id)
    elif filter == "completed":
        tasks = await TaskRepository.get_completed(user_id)
    else:
        tasks = await TaskRepository.get_all_by_user(user_id)
    
    # Получаем счётчики
    counts = await TaskRepository.get_counts(user_id)
    
    return TaskListResponse(
        tasks=[
            TaskResponse(
                id=t.id,
                text=t.text,
                category=t.category,
                event_at=t.event_at.isoformat() if t.event_at else None,
                remind_at=t.remind_at.isoformat() if t.remind_at else None,
                reminder_offset_minutes=t.reminder_offset_minutes,
                completed=t.completed,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat()
            )
            for t in tasks
        ],
        counts=counts
    )


@router.get("/counts", response_model=CountsResponse)
async def get_counts(user_id: int = Depends(get_user_id)):
    """Получить счётчики задач"""
    counts = await TaskRepository.get_counts(user_id)
    return CountsResponse(**counts)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    user_id: int = Depends(get_user_id)
):
    """Получить задачу по ID"""
    task = await TaskRepository.get_by_id(task_id, user_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task.id,
        text=task.text,
        category=task.category,
        event_at=task.event_at.isoformat() if task.event_at else None,
        remind_at=task.remind_at.isoformat() if task.remind_at else None,
        reminder_offset_minutes=task.reminder_offset_minutes,
        completed=task.completed,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@router.post("", response_model=MessageResponse)
async def create_task(
    task: TaskCreate,
    user_id: int = Depends(get_user_id)
):
    """Создать новую задачу"""
    task_id = await TaskRepository.create(
        user_id=user_id,
        text=task.text,
        category=task.category,
        event_at=task.event_at,
        reminder_offset_minutes=task.reminder_offset_minutes,
        remind_at=task.remind_at
    )
    
    return MessageResponse(
        status="created",
        message="Task created successfully",
        id=task_id
    )


@router.put("/{task_id}", response_model=MessageResponse)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    user_id: int = Depends(get_user_id)
):
    """Обновить задачу"""
    # Проверяем существование
    existing = await TaskRepository.get_by_id(task_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Обновляем
    success = await TaskRepository.update(
        task_id=task_id,
        user_id=user_id,
        text=task.text,
        category=task.category,
        event_at=task.event_at,
        reminder_offset_minutes=task.reminder_offset_minutes,
        remind_at=task.remind_at,
        completed=task.completed
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")
    
    return MessageResponse(
        status="updated",
        message="Task updated successfully"
    )


@router.post("/toggle", response_model=MessageResponse)
async def toggle_task(
    data: TaskToggle,
    user_id: int = Depends(get_user_id)
):
    """Переключить статус выполнения"""
    success = await TaskRepository.toggle_completed(data.task_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return MessageResponse(
        status="toggled",
        message="Task status toggled"
    )


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: int,
    user_id: int = Depends(get_user_id)
):
    """Удалить задачу"""
    success = await TaskRepository.delete(task_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return MessageResponse(
        status="deleted",
        message="Task deleted successfully"
    )
