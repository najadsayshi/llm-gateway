from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx
from app.config import settings
from app.routers.chat import router as chat_router





@asynccontextmanager
async def lifespan(app: FastAPI):

    client =  httpx.AsyncClient(
        base_url= settings.openai_api_base,
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"},
        timeout=httpx.Timeout(settings.request_timeout, connect=5.0),


    ) 
    app.state.client=client

    yield

    await client.aclose()

app = FastAPI(title="LLM Gateway",
              lifespan=lifespan,)

app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
