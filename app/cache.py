import hashlib
import json

CACHE_PREFIX = "cache:"
CACHE_TTL = 3600   


def make_cache_key(payload: dict) -> str:

    payload_json = json.dumps(payload,sort_keys=True)

    hashed_payload = hashlib.sha256(payload_json.encode()).hexdigest()
    cache_final = f'{CACHE_PREFIX}{hashed_payload}'
    return cache_final


async def get_cached_response(redis_client, key: str) -> dict | None:
    cached_data = await redis_client.get(key)
    if cached_data is None:
        return None
    return json.loads(cached_data)
async def set_cached_response(redis_client, key: str, response_data: dict) -> None:

    await redis_client.set(key,json.dumps(response_data),ex=CACHE_TTL)
    