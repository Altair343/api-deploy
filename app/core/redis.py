from redis.asyncio import (Redis, RedisCluster)
from app.core.config import get_settings

settings = get_settings()

def remap_address( address: tuple[str, int]) -> tuple[str, int]:
    _, port = address
    return settings.REDIS_HOST, port

# redis_client = Redis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     password=settings.REDIS_PASSWORD,
#     ssl=True,
#     decode_responses=True,
#     socket_connect_timeout=10,
#     socket_timeout=10,
# )

redis_client = RedisCluster(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    ssl=True,
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=10,

    ssl_cert_reqs="required",
    ssl_check_hostname=True,
    address_remap=remap_address,

    socket_keepalive=True,
    max_connections=20
)

async def close_redis() -> None:
    await redis_client.aclose()