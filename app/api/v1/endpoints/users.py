from fastapi import APIRouter, HTTPException, status
from app.api.dependencies import (UserServiceDep, CurrentUserDep)
from app.schemas.user import UserRead

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def get_my_profile(current_user: CurrentUserDep):
    return current_user

# @router.get("/{user_id}", response_model=UserRead)
# async def get_user(user_id: int, service: UserServiceDep):
#     user = await service.get_user(user_id)
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found",
#         )
#     return user

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, current_user: CurrentUserDep):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return current_user