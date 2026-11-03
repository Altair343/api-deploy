from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.reset_tokens import (
    generate_reset_token,
    hash_reset_token,
)
from app.core.security import hash_password_async
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.email.base import EmailSender


class InvalidResetTokenError(Exception):
    pass


class PasswordResetService:
    def __init__(self, session: AsyncSession, email_sender: EmailSender) -> None:
        self.session = session
        self.email_sender = email_sender
        self.settings = get_settings()

    async def request_reset(self, email: str) -> None:
        token = None

        async with self.session.begin():
            result = await self.session.execute(
                select(User).where(
                    User.email == email.strip().lower()
                )
            )

            user = result.scalar_one_or_none()

            if user is not None and user.is_active:
                token = generate_reset_token()

                reset = PasswordResetToken(
                    user_id=user.id,
                    token_hash=hash_reset_token(token),
                    expires_at=(
                        datetime.now(timezone.utc)
                        + timedelta(
                            minutes=self.settings
                            .PASSWORD_RESET_EXPIRE_MINUTES
                        )
                    ),
                )

                self.session.add(reset)

        if token is None:
            return

        # The token has already been committed.
        query = urlencode({"token": token})
        separator = (
            "&"
            if "?" in self.settings.PASSWORD_RESET_URL
            else "?"
        )

        reset_url = (
            f"{self.settings.PASSWORD_RESET_URL}"
            f"{separator}{query}"
        )

        await self.email_sender.send_password_reset(
            recipient=email.strip().lower(),
            reset_url=reset_url,
            expires_minutes=(
                self.settings.PASSWORD_RESET_EXPIRE_MINUTES
            ),
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        token_hash = hash_reset_token(token)

        # Argon2 is CPU-intensive; calculate outside
        # the database transaction.
        new_hash = await hash_password_async(new_password)

        async with self.session.begin():
            # Find the token's owner.
            lookup = await self.session.execute(
                select(PasswordResetToken.user_id)
                .where(
                    PasswordResetToken.token_hash
                    == token_hash
                )
            )

            user_id = lookup.scalar_one_or_none()

            if user_id is None:
                raise InvalidResetTokenError()

            # Serialize resets for the same user.
            user_result = await self.session.execute(
                select(User)
                .where(User.id == user_id)
                .with_for_update()
            )

            user = user_result.scalar_one_or_none()

            if user is None or not user.is_active:
                raise InvalidResetTokenError()

            # Re-read the token after acquiring the lock.
            token_result = await self.session.execute(
                select(PasswordResetToken)
                .where(
                    PasswordResetToken.token_hash
                    == token_hash
                )
                .with_for_update()
            )

            reset = token_result.scalar_one_or_none()
            now = datetime.now(timezone.utc)

            if (
                reset is None
                or reset.used_at is not None
                or reset.expires_at <= now
                or reset.user_id != user.id
            ):
                raise InvalidResetTokenError()

            user.hashed_password = new_hash

            # Invalidate all outstanding reset tokens.
            await self.session.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                )
                .values(used_at=now)
            )
