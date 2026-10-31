from sqlalchemy.ext.asyncio import AsyncSession
from app.pricing import calculate_cost
from app.models import UsageRecord
from sqlalchemy import select, func

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


async def get_usage_summary(session: AsyncSession, api_key_id: int) -> list[dict]:

    stmt = (
    select(
        UsageRecord.model,
        func.count(UsageRecord.id).label("requests"),
        func.sum(UsageRecord.prompt_tokens).label("prompt_tokens"),
        func.sum(UsageRecord.completion_tokens).label("completion_tokens"),
        func.sum(UsageRecord.total_tokens).label("total_tokens"),
        func.sum(UsageRecord.cost).label("cost"),
    )
    .where(UsageRecord.api_key_id == api_key_id)
    .group_by(UsageRecord.model)
)
    result = await session.execute(stmt)
    return result.mappings().all()                        # dict-like rows directly

