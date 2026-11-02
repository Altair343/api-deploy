
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.dependencies import ( AuthServiceDep, UserServiceDep)
from app.core.exceptions import ( InvalidCredentialsError, UserAlreadyExistsError)
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserRead

from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

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


@router.post( "/login", response_model=TokenResponse)
async def login( data: LoginRequest, service: AuthServiceDep):
    try:
        token = await service.authenticate(
            email=str(data.email),
            password=data.password,
        )

        return TokenResponse(access_token=token)

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

@router.post( "/token", response_model=TokenResponse)
async def oauth2_token(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    service: AuthServiceDep,
):
    try:
        token = await service.authenticate(
            email=form_data.username,
            password=form_data.password,
        )

        return TokenResponse(access_token=token)

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc