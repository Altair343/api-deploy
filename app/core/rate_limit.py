
import hashlib
import hmac
import math
import time
from redis.asyncio import (Redis,RedisCluster)
from app.core.config import get_settings

RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
    redis.call("PEXPIRE", KEYS[1], ARGV[1])
end
local ttl = redis.call("PTTL", KEYS[1])
return {current, ttl}
"""

class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


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
