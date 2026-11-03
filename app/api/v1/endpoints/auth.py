
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.dependencies import ( AuthServiceDep, UserServiceDep)
from app.core.exceptions import ( InvalidCredentialsError, UserAlreadyExistsError)
from app.schemas.auth import TokenPair
from app.schemas.user import UserCreate, UserRead

from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from fastapi import Request
from redis.exceptions import RedisError
from app.api.dependencies import (LoginRateLimiterDep, LoginRateLimiter)
from app.core.rate_limit import RateLimitExceeded

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
