from datetime import datetime, timedelta, timezone
import anyio
import jwt
from uuid import UUID
from pwdlib import PasswordHash
from anyio import CapacityLimiter
from app.core.config import get_settings

from dataclasses import dataclass
from jwt import InvalidTokenError
from app.core.exceptions import InvalidAccessTokenError

password_hash = PasswordHash.recommended()

# Maximum number of concurrent Argon2 operations
# per application process.
argon2_limiter = CapacityLimiter(2)

def hash_password(password: str) -> str:
    """
    Generate a secure password hash using Argon2.
    """
    return password_hash.hash(password)

# Valid Argon2id hash of a dummy password.
# It does not represent a real account.
DUMMY_PASSWORD_HASH = hash_password(
    "dummy-password-never-used-for-login"
)

def verify_password( plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its stored hash.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

async def hash_password_async(password: str) -> str:
    return await anyio.to_thread.run_sync(
        hash_password,
        password,
        limiter=argon2_limiter,
    )

async def verify_password_async( plain_password: str, hashed_password: str) -> bool:
    return await anyio.to_thread.run_sync(
        verify_password,
        plain_password,
        hashed_password,
        limiter=argon2_limiter,
    )

def create_access_token( user_id: int, session_id: UUID) -> str:
    """
    Create a signed JWT access token.
    """
    settings = get_settings()

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "sid": str(session_id),
        "exp": expires_at,
        "type": "access"
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

@dataclass(frozen=True)
class AccessTokenPayload:
    user_id: int
    session_id: UUID

def decode_access_token(token: str) -> AccessTokenPayload:
    """
    Validate an access token and return its user ID.
    Raises jwt.InvalidTokenError when validation fails.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "require": ["sub", "iat", "exp", "type","sid"],
            },
        )

        if payload.get("type") != "access":
            raise InvalidAccessTokenError()

        user_id = int(payload["sub"])
        session_id = UUID(payload["sid"])

        if user_id <= 0:
            raise InvalidAccessTokenError()

        return AccessTokenPayload(
            user_id=user_id,
            session_id=session_id,
        )

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        raise InvalidAccessTokenError() from exc
