from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config import settings
from app.providers.registry import PROVIDERS
from app.routers.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    clients = {}

    for provider in PROVIDERS:
        if not provider.api_key:
            continue

        clients[provider.name] = httpx.AsyncClient(
            base_url=provider.base_url,
            headers={"Authorization": f"Bearer {provider.api_key}"},
            timeout=httpx.Timeout(settings.request_timeout, connect=5.0),
        )

    app.state.clients = clients

    yield

    for client in clients.values():
        await client.aclose()


app = FastAPI(title="LLM Gateway", lifespan=lifespan)

app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok", "providers": sorted(app.state.clients)}
