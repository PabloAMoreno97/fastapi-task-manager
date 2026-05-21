import uuid
from typing import Optional

from fastapi import HTTPException, status

from src.db.models.task import TaskPriority, TaskStatus
from src.repositories.task_repo import TaskRepository
from src.schemas.task import TaskCreate, TaskListResponse, TaskOut, TaskUpdate


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def list_tasks(
        self,
        user_id: uuid.UUID,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> TaskListResponse:
        total, items = await self.repo.list_by_user(user_id, status, priority, offset, limit)
        return TaskListResponse(total=total, items=[TaskOut.model_validate(t) for t in items])

    async def create_task(self, user_id: uuid.UUID, data: TaskCreate) -> TaskOut:
        task = await self.repo.create(
            user_id=user_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
        )
        return TaskOut.model_validate(task)

    async def get_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskOut:
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        return TaskOut.model_validate(task)

    async def update_task(self, task_id: uuid.UUID, user_id: uuid.UUID, data: TaskUpdate) -> TaskOut:
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        updates = data.model_dump(exclude_unset=True)
        task = await self.repo.update(task, **updates)
        return TaskOut.model_validate(task)

    async def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        await self.repo.delete(task)
