from typing import Annotated
import jwt

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.user import UserService
from app.services.auth import AuthService

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import (decode_access_token, InvalidAccessTokenError)
from app.models.user import User
from app.repositories.user import UserRepository

from app.core.rate_limit import (LoginRateLimiter, PasswordResetRateLimiter)
from app.core.redis import redis_client
from sqlalchemy import select
from app.services.session import SessionService

SessionDep = Annotated[
    AsyncSession,
    Depends(get_session),
]

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)

def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

def get_login_rate_limiter() -> LoginRateLimiter:
    return LoginRateLimiter(redis_client)

async def get_current_user( token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    # Validate the JWT.
    try:
        payload = decode_access_token(token)
    except InvalidAccessTokenError as exc:
        raise credentials_exception() from exc

    # Validate the associated session.
    session_service = SessionService(session)

    active_session = await session_service.get_active_session(
        session_id=payload.session_id,
        user_id=payload.user_id,
    )

    if active_session is None:
        raise credentials_exception()

    # Validate the user.
    result = await session.execute(
        select(User).where(
            User.id == payload.user_id,
            User.is_active.is_(True),
        )
    )

    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception()
    return user


def get_password_reset_rate_limiter() -> PasswordResetRateLimiter:
    return PasswordResetRateLimiter(redis_client)

PasswordResetRateLimiterDep = Annotated[
    PasswordResetRateLimiter,
    Depends(get_password_reset_rate_limiter),
]

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