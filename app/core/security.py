from datetime import datetime, timedelta, timezone
import anyio
import jwt
from pwdlib import PasswordHash
from anyio import CapacityLimiter
from app.core.config import get_settings

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

def create_access_token(user_id: int) -> str:
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
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """
    Validate an access token and return its user ID.

    Raises jwt.InvalidTokenError when validation fails.
    """
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={
            "require": ["sub", "iat", "exp", "type"],
        },
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError(
            "Invalid token type"
        )

    subject = payload["sub"]

    if (
        not isinstance(subject, str)
        or not subject.isdecimal()
        or int(subject) <= 0
    ):
        raise jwt.InvalidTokenError(
            "Invalid token subject"
        )

    return int(subject)
