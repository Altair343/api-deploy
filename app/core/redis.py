from redis.asyncio import Redis
from app.core.config import get_settings

settings = get_settings()

redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)

async def close_redis() -> None:
    await redis_client.aclose()