from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi_pagination import add_pagination

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from app.dependencies import get_db
from app.models import Task, User, StatusRole
from app.models import User as UserModel
from app.schemas import TaskResponse, TaskCreate, AllTasksResponse
from app.email_utils import send_email_mock
from auth.dependencies import get_current_user, role_required
from auth.routes import router as auth_router

# Initialize FastAPI app
app = FastAPI(
    title="Task Tracker",
    description="This project is a simplified backend for a team task tracker similar to Trello or Jira. "
                "It allows users to read, create, edit, and delete tasks with various attributes "
                "and includes basic role-based authorization and mock email notifications."
)

# Include authentication routes from the auth module
app.include_router(auth_router, prefix="/auth", tags=["auth"])


async def get_task_or_404(task_id: int, session: AsyncSession):
    query = select(Task).where(Task.id == task_id).options(selectinload(Task.assignees))
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


async def get_user_or_404(user_id: int, session: AsyncSession):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def verify_assignees_exist(assignees_ids: list[int], session: AsyncSession):
    # Fetch assignees from the database
    result = await session.execute(
        select(User).where(User.id.in_(assignees_ids))
    )
    assignees = result.scalars().all()

    # Get the IDs of the fetched assignees
    assignees_id = {user.id for user in assignees}

    # Find missing assignees
    missing_assignees = set(assignees_ids) - assignees_id
    if missing_assignees:
        raise HTTPException(
            status_code=404,
            detail=f"Assignees with IDs {', '.join(map(str, missing_assignees))} not found",
        )

    return assignees


# Endpoint to get all tasks with pagination
@app.get("/tasks/", response_model=AllTasksResponse, status_code=200)
async def read_tasks(
        session: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
        page: int = Query(1, ge=1),  # Page number, default is 1
        size: int = Query(10, ge=1, le=100),  # Page size, default is 10, max 100
):
    """
    Retrieve a paginated list of tasks.

    - **page**: Page number to retrieve (default is 1).
    - **size**: Number of tasks per page (default is 10, max 100).
    """
    offset = (page - 1) * size  # Calculate the offset for pagination
    query = (select(Task).options(selectinload(Task.assignees)).offset(offset).limit(size))

    # Fetch tasks with assignees
    result = await session.execute(query)
    tasks = result.scalars().all()

    # If not tasks are found, raise error
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    # Transform tasks to TaskResponse, converting assignees to a list of IDs
    task_responses = []
    for task in tasks:
        task_responses.append(
            {
                "id": task.id,
                "title": task.title,
                "responsible_person_id": task.responsible_person_id,
                "assignees": [user.id for user in task.assignees],
                "status": task.status,
                "priority": task.priority,
            }
        )

    # Build pagination info
    pagination_info = {
        "page": page,
        "size": size,
        "total": len(tasks),
    }

    return {
        "pagination": pagination_info,
        "tasks": task_responses,
    }


# Endpoint to get a specific task by ID
@app.get("/tasks/{task_id}", response_model=TaskResponse, status_code=200)
async def read_task(
        task_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
    Retrieve a specific task by its ID.

    - **task_id**: ID of the task to retrieve.
    """
    task = await get_task_or_404(task_id, session)

    task_response = {
        "id": task.id,
        "title": task.title,
        "responsible_person_id": task.responsible_person_id,
        "assignees": [user.id for user in task.assignees],
        "status": task.status,
        "priority": task.priority,
    }

    return task_response


# Endpoint to create a new task
@app.post("/tasks/", response_model=TaskResponse, status_code=201)
async def create_task(
        task_create: TaskCreate,
        session: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new task.

     **Request Body:**

    - **title** (string): The title of the task.
    - **responsible_person_id** (integer): The ID of the user responsible for the task.
    - **assignees** (array of integers): A list of user IDs assigned to the task.
    - **status** (string): The status of the task. Valid values are "TODO", "In progress", "Done".
    - **priority** (integer): The priority level of the task.

    **Example Request Body:**

    ```json
    {
      "title": "Fix login bug",
      "responsible_person_id": 1,
      "assignees": [2, 3],
      "status": "TODO",
      "priority": 1
    }
    ```
    """

    # Ensure that responsible person exists in DB
    responsible_person = await get_user_or_404(task_create.responsible_person_id, session)

    # Create new task
    new_task = Task(
        title=task_create.title,
        responsible_person=responsible_person,
        status=task_create.status,
        priority=task_create.priority,
    )

    # Fetch all assignees for the task
    assignees = await verify_assignees_exist(task_create.assignees, session)

    new_task.assignees.extend(assignees)

    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)  # Refresh the task to get the updated values

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


# Endpoint to update existing task by ID
@app.put("/tasks/{task_id}", response_model=TaskResponse, status_code=200)
async def update_task(
        task_id: int,
        task_update: TaskCreate,
        session: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
    Update an existing task in the task tracker.

    **Parameters:**

    - **task_id** (integer): The ID of the task to be updated. This ID should correspond to an existing task in the database.

    **Request Body:**

    - **title** (string): The updated title of the task.
    - **responsible_person_id** (integer): The updated ID of the user responsible for the task.
    - **assignees** (array of integers): A list of user IDs to be assigned to the task. The list can be empty.
    - **status** (string): The updated status of the task. Valid values are "TODO", "In progress", "Done".
    - **priority** (integer): The updated priority level of the task.

    **Example Request Body:**

    ```json
    {
      "title": "Update login bug fix",
      "responsible_person_id": 2,
      "assignees": [3, 4],
      "status": "In progress",
      "priority": 2
    }
    ```
    """
    task = await get_task_or_404(task_id, session)

    # Ensure that responsible person exists in DB
    responsible_person = await get_user_or_404(task_update.responsible_person_id, session)

    # Fetch the assignees for the updated tasks
    assignees = await verify_assignees_exist(task_update.assignees, session)

    # Send email notification if the task status has changed
    if task.status != task_update.status:
        subject = f"Task '{task.title}' status updated"
        body = f"Dear {responsible_person.username}, the status of the task '{task.title}' has been changed to {task_update.status}."
        send_email_mock(responsible_person.username + "@example.com", subject, body)

    # Update the task with the provided data
    task.title = task_update.title
    task.responsible_person_id = task_update.responsible_person_id
    task.assignees = assignees
    task.status = task_update.status
    task.priority = task_update.priority

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


# Endpoint to delete task by ID
@app.delete("/tasks/{task_id}", response_model=dict, status_code=200)
async def delete_task(
        task_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(
            role_required(StatusRole.ADMIN)
        ),
):
    """
    Delete a task by its ID.

    - **task_id**: ID of the task to delete.
    """
    task = await get_task_or_404(task_id, session)

    await session.delete(task)
    await session.commit()
    return {"detail": "Task deleted successfully"}


add_pagination(app)
