

from fastapi import APIRouter, Depends
from app.usage import get_usage_summary
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import APIKey
from app.auth import get_api_key
from app.db import get_session


router = APIRouter()


@router.get("/v1/usage")
async def get_usage(
    api_key: APIKey = Depends(get_api_key),
    session: AsyncSession = Depends(get_session),
):
    usage_summary = await get_usage_summary(session, api_key.id)
    return {"data": [{**row, "cost": str(row["cost"])} for row in usage_summary]}
