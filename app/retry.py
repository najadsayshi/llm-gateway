
import random
import asyncio


RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def should_retry(status_code: int) -> bool:

    if status_code in RETRYABLE_STATUSES:
        return True
    return False


MAX_ATTEMPTS = 3
BASE_DELAY = 0.5




async def retry_delay(attempt: int) -> None:
    """Sleep before the next attempt. attempt is 0 for the first retry."""
    delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.3)
    await asyncio.sleep(delay)