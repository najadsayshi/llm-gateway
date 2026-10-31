from sqlalchemy.ext.asyncio import AsyncSession
from app.pricing import calculate_cost
from app.models import UsageRecord

async def record_usage(session: AsyncSession,api_key_id: int,model: str,provider: str,usage: dict,) -> None:
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    usage_record = UsageRecord(
        api_key_id=api_key_id,
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost=cost,
    )
    session.add(usage_record)
    await session.commit()
