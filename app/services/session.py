from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.refresh_tokens import (generate_refresh_token, hash_refresh_token)
from app.models.user_session import UserSession

class InvalidRefreshTokenError(Exception):
    pass

class SessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def create_session( self, user_id: int) -> tuple[UserSession, str]:
        token = generate_refresh_token()

        user_session = UserSession(
            user_id=user_id,
            refresh_token_hash=hash_refresh_token(token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(
                    days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
                )
            ),
        )

        self.session.add(user_session)
        await self.session.flush()
        return user_session, token

    async def rotate_refresh_token(self, refresh_token: str) -> tuple[UserSession, str]:
        token_hash = hash_refresh_token(refresh_token)

        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.refresh_token_hash == token_hash
            )
            .with_for_update()
        )

        user_session = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if (
            user_session is None
            or user_session.revoked_at is not None
            or user_session.expires_at <= now
        ):
            raise InvalidRefreshTokenError()

        new_token = generate_refresh_token()
        user_session.refresh_token_hash = (
            hash_refresh_token(new_token)
        )

        await self.session.flush()
        return user_session, new_token

    async def revoke_session(self, session_id: UUID, user_id: int) -> None:
        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
            )
            .with_for_update()
        )

        user_session = result.scalar_one_or_none()
        if user_session is not None:
            user_session.revoked_at = datetime.now(timezone.utc)
