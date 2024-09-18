from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi_pagination import add_pagination
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from smtplib import SMTPException

from app.dependencies import get_db
from app.models import Task, User, StatusRole
from app.models import User as UserModel
from auth.dependencies import get_current_user
from auth.routes import router as auth_router
from app.schemas import TaskResponse, TaskCreate, AllTasksResponse

app = FastAPI(title="Task Tracker")

# Include authentication routes from the auth module
app.include_router(auth_router, prefix="/auth", tags=["auth"])


def send_email_mock(to_email: str, subject: str, body: str):
    # Mock up of sending Email
    try:
        print(f"Sending email to {to_email}")
        print(f"Subject: {subject}")
        print(f"Body {body}")
        return True
    except SMTPException as e:
        print(f"Error sending email: {e}")
        return False


def role_required(required_role: StatusRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Action requires '{required_role.value}' role",
            )
        return current_user

    return role_checker


# Get all tasks
@app.get("/tasks/", response_model=AllTasksResponse, status_code=200)
async def read_tasks(session: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user),
                     page: int = Query(1, ge=1),  # Page number, default is 1
                     size: int = Query(10, ge=1, le=100)
                     ):
    offset = (page - 1) * size
    query = select(Task).options(selectinload(Task.assignees)).offset(offset).limit(
        size)  # Загружаем связанные объекты асинхронно
    result = await session.execute(query)
    tasks = result.scalars().all()

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    # Transform tasks to TaskResponse, converting assignees to a list of IDs
    task_responses = []
    for task in tasks:
        task_responses.append({
            "id": task.id,
            "title": task.title,
            "responsible_person_id": task.responsible_person_id,
            "assignees": [user.id for user in task.assignees],
            "status": task.status,
            "priority": task.priority,
        })

    pagination_info = {
        "page": page,
        "size": size,
        "total": tasks,
    }

    return {
        "pagination": pagination_info,
        "tasks": task_responses,
    }


# Get specific task by ID
@app.get("/tasks/{task_id}", response_model=TaskResponse, status_code=200)
async def read_task(task_id: int, session: AsyncSession = Depends(get_db),
                    current_user: UserModel = Depends(get_current_user)):
    query = select(Task).options(selectinload(Task.assignees)).where(Task.id == task_id)
    result = await session.execute(query)
    task = result.scalars().first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task_response = {
        "id": task.id,
        "title": task.title,
        "responsible_person_id": task.responsible_person_id,
        "assignees": [user.id for user in task.assignees],
        "status": task.status,
        "priority": task.priority,
    }

    return task_response


# Create
@app.post("/tasks/", response_model=TaskResponse, status_code=201)
async def create_task(task_create: TaskCreate, session: AsyncSession = Depends(get_db),
                      current_user: UserModel = Depends(get_current_user)):
    result = await session.execute(select(User).where(User.id == task_create.responsible_person_id))
    responsible_person = result.scalar_one_or_none()
    if not responsible_person:
        raise HTTPException(status_code=404, detail="Responsible person not found")

    # Create new task
    new_task = Task(
        title=task_create.title,
        responsible_person=responsible_person,
        status=task_create.status,
        priority=task_create.priority,
    )

    result = await session.execute(select(User).where(User.id.in_(task_create.assignees)))
    assignees = result.scalars().all()

    # Check if all assignees exist
    assignees_id = {user.id for user in assignees}
    missing_assignees = set(task_create.assignees) - assignees_id
    if missing_assignees:
        raise HTTPException(status_code=404,
                            detail=f"Assignees with IDs {', '.join(map(str, missing_assignees))} not found")

    new_task.assignees.extend(assignees)

    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    # Build the response data
    task_response = {
        "id": new_task.id,
        "title": new_task.title,
        "responsible_person_id": new_task.responsible_person_id,
        "assignees": [user.id for user in new_task.assignees],
        "status": new_task.status,
        "priority": new_task.priority,
    }

    return task_response


@app.put("/tasks/{task_id}", response_model=TaskResponse, status_code=200)
async def update_task(task_id: int,
                      task_update: TaskCreate,
                      session: AsyncSession = Depends(get_db),
                      current_user: UserModel = Depends(get_current_user)
                      ):
    # Fetch the existing task
    query = select(Task).where(Task.id == task_id).options(selectinload(Task.assignees))
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Отримуємо відповідальну особу
    responsible_person_query = select(User).where(User.id == task.responsible_person_id)
    resp_result = await session.execute(responsible_person_query)
    responsible_person = resp_result.scalar_one_or_none()

    if not responsible_person:
        raise HTTPException(status_code=404, detail="Responsible person not found")

    # Fetch the assignees
    assignees_query = select(User).where(User.id.in_(task_update.assignees))
    assignees_result = await session.execute(assignees_query)
    assignees = assignees_result.scalars().all()

    # Check if all assignees exist
    assignees_id = {user.id for user in assignees}
    missing_assignees = set(task_update.assignees) - assignees_id
    if missing_assignees:
        raise HTTPException(status_code=404,
                            detail=f"Assignees with IDs {', '.join(map(str, missing_assignees))} not found")

    # Перевірка зміни статусу
    if task.status != task_update.status:
        # Відправка імейлу (мокап)
        subject = f"Task '{task.title}' status updated"
        body = f"Dear {responsible_person.username}, the status of the task '{task.title}' has been changed to {task_update.status}."
        send_email_mock(responsible_person.username + "@example.com", subject, body)

    # Update the task with the provided data
    task.title = task_update.title
    task.responsible_person_id = task_update.responsible_person_id

    # Update task's responsible person and assignees
    task.assignees = assignees
    task.status = task_update.status
    task.priority = task_update.priority

    # Commit changes
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # Build the response data
    task_response = {
        "id": task.id,
        "title": task.title,
        "responsible_person_id": task.responsible_person_id,
        "assignees": [user.id for user in task.assignees],
        "status": task.status,
        "priority": task.priority,
    }

    return task_response


# Delete
@app.delete("/tasks/{task_id}", response_model=dict, status_code=200)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_db),
                      current_user: UserModel = Depends(role_required(StatusRole.ADMIN, StatusRole.MANAGER))):
    result = await session.execute(select(Task).filter(Task.id == task_id))
    db_task = result.scalars().first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(db_task)
    await session.commit()
    return {"detail": "Task deleted successfully"}


add_pagination(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True)
