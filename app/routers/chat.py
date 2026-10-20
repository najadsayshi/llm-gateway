import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask

from app.providers.compatible import chat_completion, open_chat_stream
from app.providers.registry import provider_for_model
from app.schemas import ChatCompletionRequest

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request):
    provider = provider_for_model(body.model)

    if provider is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"message": f"Unknown model: {body.model}",
                               "type": "model_not_found", "param": "model"}},
        )

    client = request.app.state.clients.get(provider.name)

    if client is None:
        return JSONResponse(
            status_code=503,
            content={"error": {"message": f"Provider '{provider.name}' is not configured",
                               "type": "provider_unavailable"}},
        )

    payload = body.model_dump(exclude_none=True)

    try:
        if body.stream:
            upstream = await open_chat_stream(client, payload)

            if upstream.status_code >= 400:
                await upstream.aread()
                error = upstream.json()
                await upstream.aclose()
                return JSONResponse(status_code=upstream.status_code, content=error)

            return StreamingResponse(
                upstream.aiter_bytes(),
                media_type="text/event-stream",
                background=BackgroundTask(upstream.aclose),
            )

        response = await chat_completion(client, payload)

        if response.status_code >= 400:
            return JSONResponse(status_code=response.status_code, content=response.json())

        return response.json()

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": {"message": "Upstream provider timed out",
                               "type": "gateway_timeout"}},
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={"error": {"message": "Could not reach upstream provider",
                               "type": "bad_gateway"}},
        )
