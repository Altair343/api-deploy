from typing import Annotated
import jwt

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.user import UserService
from app.services.auth import AuthService

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user import UserRepository

from app.core.rate_limit import LoginRateLimiter
from app.core.redis import redis_client

SessionDep = Annotated[
    AsyncSession,
    Depends(get_session),
]

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

def get_login_rate_limiter() -> LoginRateLimiter:
    return LoginRateLimiter(redis_client)

async def get_current_user( token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    credentials_exception = HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc

    repository = UserRepository(session)
    user = await repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]

AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]

CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]

LoginRateLimiterDep = Annotated[
    LoginRateLimiter,
    Depends(get_login_rate_limiter),
]