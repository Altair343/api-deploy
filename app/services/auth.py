from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidCredentialsError
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> str:
        user = await self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError(
                "Invalid email or password 1"
            )

        if not user.is_active or not user.hashed_password:
            raise InvalidCredentialsError(
                "Invalid email or password 2"
            )

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise InvalidCredentialsError(
                "Invalid email or password 3"
            )

        return create_access_token(user.id)
