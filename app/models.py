from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base
import enum

# additional model for relationship "many-to-many"
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),  # Foreign key to the 'tasks' table
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),  # Foreign key to the 'users' table
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

    # One-to-many relationship with Task (responsible_person_id in Task refers to User.id)
    tasks = relationship("Task", back_populates="responsible_person", lazy="selectin")

    # Many-to-many relationship with Task (via the task_assignees association table)
    assigned_tasks = relationship(
        "Task", secondary=task_assignees, back_populates="assignees", lazy="selectin"
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    responsible_person_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(TaskStatusEnum, name="status_task"), nullable=False)
    priority = Column(Integer)

    # One-to-many relationship with User (responsible_person_id in Task refers to User.id)
    responsible_person = relationship("User", back_populates="tasks", lazy="selectin")

    # Many-to-many relationship with User (via the task_assignees association table)
    assignees = relationship(
        "User",
        secondary=task_assignees,
        back_populates="assigned_tasks",
        lazy="selectin",
    )
