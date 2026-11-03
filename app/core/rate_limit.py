
import hashlib
import hmac
import math
from redis.asyncio import (Redis,RedisCluster)
from app.core.config import get_settings
from app.core.exceptions import RateLimitExceeded

RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
    redis.call("PEXPIRE", KEYS[1], ARGV[1])
end
local ttl = redis.call("PTTL", KEYS[1])
return {current, ttl}
"""

class LoginRateLimiter:
    def __init__(self, redis: RedisCluster):
        self.redis = redis
        self.settings = get_settings()

    def _account_key(self, email: str) -> str:
        normalized = email.strip().lower()

        digest = hmac.new(
            self.settings.SECRET_KEY.encode("utf-8"),
            normalized.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return f"rate_limit:login:account:{digest}"

    async def _check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        count, ttl_ms = await self.redis.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds * 1000,
        )

        if count > limit:
            retry_after = max(
                1,
                math.ceil(ttl_ms / 1000),
            )
            raise RateLimitExceeded(retry_after)

    async def check_login(
        self,
        ip_address: str,
        email: str,
    ) -> None:
        await self._check(
            key=f"rate_limit:login:ip:{ip_address}",
            limit=self.settings.LOGIN_RATE_LIMIT_IP,
            window_seconds=self.settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        )

        await self._check(
            key=self._account_key(email),
            limit=self.settings.LOGIN_RATE_LIMIT_ACCOUNT,
            window_seconds=self.settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        )

class PasswordResetRateLimiter:
    def __init__(self, redis: RedisCluster):
        self.redis = redis
        self.settings = get_settings()

    async def _check(
        self,
        key: str,
        limit: int,
    ) -> None:
        count, ttl_ms = await self.redis.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            self.settings.PASSWORD_RESET_WINDOW_SECONDS
            * 1000,
        )

        if count > limit:
            raise RateLimitExceeded(
                max(1, math.ceil(ttl_ms / 1000))
            )

    def _account_key(self, email: str) -> str:
        normalized = email.strip().lower()

        digest = hmac.new(
            self.settings.SECRET_KEY.encode(),
            normalized.encode(),
            hashlib.sha256,
        ).hexdigest()

        return (
            "rate_limit:password_reset:account:"
            f"{digest}"
        )

    async def check_request(
        self,
        ip_address: str,
        email: str,
    ) -> None:
        await self._check(
            f"rate_limit:password_reset:request:ip:{ip_address}",
            self.settings.PASSWORD_RESET_REQUEST_LIMIT_IP,
        )

        await self._check(
            self._account_key(email),
            self.settings.PASSWORD_RESET_REQUEST_LIMIT_ACCOUNT,
        )

    async def check_reset(
        self,
        ip_address: str,
    ) -> None:
        await self._check(
            f"rate_limit:password_reset:attempt:ip:{ip_address}",
            self.settings.PASSWORD_RESET_ATTEMPT_LIMIT_IP,
        )
