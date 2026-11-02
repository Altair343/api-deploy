from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import UserServiceDep
from app.core.exceptions import UserAlreadyExistsError
from app.schemas.user import UserCreate, UserRead


router = APIRouter()

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED )
async def create_user( data: UserCreate, service: UserServiceDep ):
    try:
        return await service.create_user(data)

    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

@router.get("/{user_id}", response_model=UserRead )
async def get_user( user_id: int, service: UserServiceDep, ):
    user = await service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
