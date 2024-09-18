from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base
import enum

# additional model for relationship "many-to-many"
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class TaskStatusEnum(enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "In progress"
    DONE = "Done"


class StatusRole(enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    DEVELOPER = "Developer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(Enum(StatusRole, name="status_role"), nullable=False)

    # relationships
    tasks = relationship("Task", back_populates="responsible_person",lazy="selectin")
    assigned_tasks = relationship("Task", secondary=task_assignees, back_populates="assignees",lazy="selectin")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    responsible_person_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(TaskStatusEnum, name="status_task"), nullable=False)
    priority = Column(Integer)

    # relationships
    responsible_person = relationship("User", back_populates="tasks", lazy="selectin")
    assignees = relationship("User", secondary=task_assignees, back_populates="assigned_tasks",lazy="selectin")
