from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dependencies import get_db
from app.models import User, StatusRole
from app.config import settings

from auth.models import TokenData
from auth.utils import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_user(db: AsyncSession, username: str):
    query = select(User).filter(User.username == username)
    result = await db.execute(query)
    return result.scalars().first()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=settings.algorithm)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Dependency to ensure that a user has the required role to perform certain actions
def role_required(required_role: StatusRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        # Check if the current user has the required role, otherwise raise a 403 error
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Action requires '{required_role.value}' role",
            )
        return current_user

    return role_checker