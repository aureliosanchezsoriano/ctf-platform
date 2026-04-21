import logging
from fastapi import HTTPException, status
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

async def check_rate_limit(
    redis: Redis,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """
    Increment a counter in Redis and raise 429 if limit exceeded.
    Uses INCR + EXPIRE pattern — atomic and TTL-based.
    """
    current = await redis.incr(key)

    if current == 1:
        # First request in this window — set the expiry
        await redis.expire(key, window_seconds)

    if current > max_requests:
        ttl = await redis.ttl(key)
        logger.warning(f"Rate limit exceeded for key: {key}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {ttl} seconds.",
            headers={"Retry-After": str(ttl)},
        )
