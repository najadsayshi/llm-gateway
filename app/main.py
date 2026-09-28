from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx
from app.config import settings





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

@app.get("/health")
async def health():
    return {"status": "ok"}
