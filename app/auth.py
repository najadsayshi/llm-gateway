
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.security import hash_api_key
from app.models import APIKey
from app.db import get_session





async def get_api_key(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> APIKey:

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )



    hashed_token = hash_api_key(token)
    stmt = select(APIKey).where(APIKey.key_hash == hashed_token)
    row = await session.scalar(stmt)

    if not row or not row.is_active:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return row