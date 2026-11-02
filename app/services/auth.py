from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidCredentialsError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    verify_password,
    verify_password_async,
)
from app.repositories.user import UserRepository



class AuthService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def authenticate(self, email: str, password: str) -> str:
        user = await self.repository.get_by_email(email)

        stored_hash = (
            user.hashed_password
            if user is not None and user.hashed_password
            else DUMMY_PASSWORD_HASH
        )

        password_is_valid = await verify_password_async(
            password,
            stored_hash,
        )

        if (
            user is None
            or not user.is_active
            or not user.hashed_password
            or not password_is_valid
        ):
            raise InvalidCredentialsError(
                "Invalid email or password"
            )

        return create_access_token(user.id)