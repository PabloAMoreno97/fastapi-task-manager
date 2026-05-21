import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.task import Task, TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[int, list[Task]]:
        base_filter = Task.user_id == user_id
        count_q = select(func.count()).select_from(Task).where(base_filter)
        items_q = select(Task).where(base_filter)

        if status:
            count_q = count_q.where(Task.status == status)
            items_q = items_q.where(Task.status == status)
        if priority:
            count_q = count_q.where(Task.priority == priority)
            items_q = items_q.where(Task.priority == priority)

        items_q = items_q.order_by(Task.created_at.desc()).offset(offset).limit(limit)

        total = (await self.session.execute(count_q)).scalar_one()
        items = list((await self.session.execute(items_q)).scalars().all())
        return total, items

    async def create(self, user_id: uuid.UUID, **kwargs) -> Task:
        task = Task(user_id=user_id, **kwargs)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(self, task: Task, **updates) -> Task:
        for key, value in updates.items():
            setattr(task, key, value)
        task.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.commit()
