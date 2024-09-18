from typing import Optional, List
from pydantic import BaseModel
from app.models import StatusRole, TaskStatusEnum


class UserBase(BaseModel):
    username: str
    role: StatusRole


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int


class TaskBase(BaseModel):
    title: str
    responsible_person_id: int
    assignees: List[int]  # IDs of the assignees
    status: TaskStatusEnum
    priority: int


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    page: int
    size: int
    total: int


class AllTasksResponse(BaseModel):
    pagination: PaginationInfo
    tasks: List[TaskResponse]
