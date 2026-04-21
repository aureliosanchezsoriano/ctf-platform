import logging
import redis.asyncio as aioredis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: aioredis.Redis = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=5,
)


async def get_redis() -> aioredis.Redis:
    try:
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise
    return redis_client
