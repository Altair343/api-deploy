from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.user import UserService
from app.services.auth import AuthService

SessionDep = Annotated[
    AsyncSession,
    Depends(get_session),
]

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]

AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]
