import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_session
from src.db.models.task import TaskPriority, TaskStatus
from src.db.models.user import User
from src.repositories.task_repo import TaskRepository
from src.schemas.task import TaskCreate, TaskListResponse, TaskOut, TaskUpdate
from src.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _service(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(TaskRepository(session))


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List your tasks with optional filters",
)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(_service),
):
    return await service.list_tasks(current_user.id, status, priority, offset, limit)


@router.post(
    "",
    response_model=TaskOut,
    status_code=201,
    summary="Create a new task",
)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(_service),
):
    return await service.create_task(current_user.id, data)


@router.get(
    "/{task_id}",
    response_model=TaskOut,
    summary="Get a single task",
    responses={404: {"description": "Task not found"}},
)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(_service),
):
    return await service.get_task(task_id, current_user.id)


@router.patch(
    "/{task_id}",
    response_model=TaskOut,
    summary="Partially update a task",
    responses={404: {"description": "Task not found"}},
)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(_service),
):
    return await service.update_task(task_id, current_user.id, data)


@router.delete(
    "/{task_id}",
    status_code=204,
    summary="Delete a task",
    responses={404: {"description": "Task not found"}},
)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(_service),
):
    await service.delete_task(task_id, current_user.id)
