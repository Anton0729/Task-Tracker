# Task Tracker

## Overview

This project is a simplified backend for a team task tracker similar to Trello or Jira. 
It allows users to read, create, edit, and delete tasks with various attributes and includes basic role-based authorization and mock email notifications.


## Features
1. **FastAPI with PostgreSQL Setup**: Build your API with FastAPI and connect to a PostgreSQL database.
2. **Docker Container with Docker Compose**: Use Docker and Docker Compose to containerize the application and database.
3. **JWT User Authentication**: Secure the API with JWT-based user authentication.
4. **Role-Based Authorization**: Control access to endpoints based on user roles (**Admin**, **Manager**, **Developer**).
5. **Manage Migrations with Alembic**: Use Alembic for managing database schema migrations.
6. **Pagination**: Implement pagination for listing tasks.
7. **Mock Email Sending**: Mock email notifications are sent to the responsible person when the task status changes.
8. **PgAdmin for Visualization**: Use PgAdmin for visualizing and managing the PostgreSQL database.
9**API Documentation in Swagger** - Provides interactive API documentation using Swagger, accessible at `/docs`.


## <ins> Setup Instructions

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/Anton0729/Task-Tracker.git
cd .\Task-Tracker\
```

### 2. Run Docker Desktop

### 3. Create .env file
Create a file named .env in the project root. You can use the provided [`.env` file](https://drive.google.com/file/d/1Fx7mHVyf5BFTxNGd8sLfsZF7iL_6xWvN/view?usp=sharing)
  as a template \
This .env file is crucial for the application to access the database credentials and other configuration settings.
```bash
docker-compose up --build
```

### 4. Build and run the container
```bash
docker-compose up --build
```

### 5. Access the Application

- Application: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- PgAdmin: http://localhost:80


### 6. Delete the container
```bash
docker-compose down
```