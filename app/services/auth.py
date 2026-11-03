from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import InvalidCredentialsError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    verify_password_async,
)
from app.repositories.user import UserRepository
from app.schemas.auth import TokenPair
from app.services.session import SessionService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
        self.session = session
        self.session_service = SessionService(session)

    async def authenticate(self, email: str, password: str) -> TokenPair:
        # Search for user.
        user = await self.repository.get_by_email(email)

        # Avoid significant differences in
        # verification time between existing
        # and non-existent accounts.
        stored_hash = (
            user.hashed_password
            if user is not None and user.hashed_password
            else DUMMY_PASSWORD_HASH
        )

        # Verify password.
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

        # Create the session and generate a refresh token.
        user_session, refresh_token = (
            await self.session_service.create_session(
                user_id=user.id,
            )
        )

        # Generate an access token associated with the session.
        access_token = create_access_token(
            user_id=user.id,
            session_id=user_session.id,
        )

        # Confirm the new session in PostgreSQL.
        await self.session.commit()

        # Return both tokens.
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
