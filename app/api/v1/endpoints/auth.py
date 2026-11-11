
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.dependencies import (
    AuthServiceDep, UserServiceDep,
    LoginRateLimiterDep, LoginRateLimiter)
from app.core.exceptions import ( InvalidCredentialsError, UserAlreadyExistsError)
from app.schemas.auth import (TokenPair, RefreshTokenRequest)
from app.schemas.user import UserCreate, UserRead

from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from fastapi import Request
from redis.exceptions import RedisError
from app.core.rate_limit import RateLimitExceeded

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.models.user import User
from app.services.session import (
    InvalidRefreshTokenError,
    SessionService,
)
from app.db.session import get_session


router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post( "/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: UserServiceDep):
    try:
        return await service.create_user(data)

    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post( "/login", response_model=TokenPair)
async def login(request: Request, data: LoginRequest, service: AuthServiceDep, limiter: LoginRateLimiterDep):
    await enforce_login_rate_limit(
        request=request,
        email=str(data.email),
        limiter=limiter,
    )

    try:
        tokens = await service.authenticate(
            email=data.email,
            password=data.password,
        )
        return tokens

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

@router.post( "/token", response_model=TokenPair)
async def oauth2_token(
    request: Request,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    service: AuthServiceDep,
    limiter: LoginRateLimiterDep
):
    await enforce_login_rate_limit(
            request=request,
            email=str(form_data.username),
            limiter=limiter,
        )

    try:
        tokens = await service.authenticate(
            email=form_data.username,
            password=form_data.password,
        )
        return tokens

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post( "/refresh", status_code=status.HTTP_200_OK )
async def refresh_access_token(data: RefreshTokenRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> TokenPair:

    session_service = SessionService(session)

    try:
        async with session.begin():

            # Validate and rotate refresh token.
            user_session, new_refresh_token = (
                await session_service.rotate_refresh_token(
                    refresh_token=data.refresh_token
                )
            )

            # Verify that the user still exists
            # and the account is active.
            result = await session.execute(
                select(User.id).where(
                    User.id == user_session.user_id,
                    User.is_active.is_(True),
                )
            )

            user_id = result.scalar_one_or_none()

            if user_id is None:
                raise InvalidRefreshTokenError()

            # Generate an access token associated
            # with the existing session.
            new_access_token = create_access_token(
                user_id=user_id,
                session_id=user_session.id,
            )

            response = TokenPair(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
            )

        # The transaction has committed.
        return response

    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc


async def enforce_login_rate_limit( request: Request, email: str, limiter: LoginRateLimiter) -> None:
    ip_address = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    try:
        await limiter.check_login(
            ip_address=ip_address,
            email=email,
        )

    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code= status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
            headers={
                "Retry-After": str(exc.retry_after)
            },
        ) from exc

    except RedisError as exc:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication temporarily unavailable",
        ) from exc
