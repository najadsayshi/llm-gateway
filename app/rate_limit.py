
from fastapi import HTTPException, Request, Depends
from app.auth  import get_api_key
from app.models import APIKey
import time

async def check_rate_limit(redis_client, key_id: int, limit: int) -> int | None:
    """Return None if the request is allowed, or seconds-to-wait if not."""

    window = int(time.time() // 60)  # Current minute window

    redis_key = f"rate_limit:{key_id}:{window}"

    count = await redis_client.incr(redis_key)

    if count == 1:
        await redis_client.expire(redis_key, 60)
    if count > limit:
        return 60 - int(time.time()) % 60
    return None



async def enforce_rate_limit(request: Request,api_key: APIKey = Depends(get_api_key),) -> APIKey:
    redis_client = request.app.state.redis
    limit = api_key.rate_limit
    wait_time = await check_rate_limit(redis_client, api_key.id, limit)
    if wait_time is not None:
        raise HTTPException(
    status_code=429,
    detail="Rate limit exceeded",
    headers={"Retry-After": str(wait_time)},
)

    return api_key