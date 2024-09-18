from .database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    """
    Dependency that provides an asynchronous database session to FastAPI endpoints.

    This function is used to inject an asynchronous database session into path operations.
    It ensures that the database schema is created and the session is properly managed
    for each request. After creating the session, it yields it to the endpoint, and
    ensures the session is closed after the request is complete.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
