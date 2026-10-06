import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.providers.openai_client import chat_completion
from app.schemas import ChatCompletionRequest

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request):
    payload = body.model_dump(exclude_none=True)

    try:
        response = await chat_completion(request.app.state.client, payload)
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": {"message": "Upstream provider timed out", "type": "gateway_timeout"}},
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={"error": {"message": "Could not reach upstream provider", "type": "bad_gateway"}},
        )

    if response.status_code >= 400:
        return JSONResponse(status_code=response.status_code, content=response.json())

    return response.json()
