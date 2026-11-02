import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.providers.compatible import chat_completion, open_chat_stream
from app.providers.registry import provider_for_model
from app.schemas import ChatCompletionRequest
from app.usage import record_usage

from fastapi import Depends
from app.models import APIKey
from app.rate_limit import enforce_rate_limit


from app.cache import make_cache_key, get_cached_response, set_cached_response #for caching



router = APIRouter()
#helper function 
def parse_response(response: httpx.Response) -> dict:
    try:
        data = response.json()
        if isinstance(data,dict):
            return data
        return {"error": {"message": "Invalid JSON response from upstream provider",
                                            "type": "invalid_response"}}
    
    except ValueError:
        return {"error": {"message": "Invalid JSON response from upstream provider",
                            "type": "invalid_response"}}

@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request,
                           api_key: APIKey = Depends(enforce_rate_limit),
                           session : AsyncSession = Depends(get_session)):
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

    #caching key and redis client
    cache_key = make_cache_key(payload)
    redis_client = request.app.state.redis

    try:

        cached_response = await get_cached_response(redis_client,cache_key)
    except Exception as e:
        print(f"Error occurred while fetching cached response: {e}")
        cached_response = None
    if cached_response is  not None:
        return JSONResponse(content=cached_response, headers={"X-Cache": "HIT"})



    try:
        if body.stream:
            upstream = await open_chat_stream(client, payload)

            if upstream.status_code >= 400:
                await upstream.aread()
                error = parse_response(upstream)
                await upstream.aclose()
                return JSONResponse(status_code=upstream.status_code, content=error)

            return StreamingResponse(
                upstream.aiter_bytes(),
                media_type="text/event-stream",
                background=BackgroundTask(upstream.aclose),
            )

        response = await chat_completion(client, payload)
        
        response_data = parse_response(response)
        if response.status_code >= 400:
            return JSONResponse(status_code=response.status_code, content= response_data)

        await record_usage(session=session,api_key_id=api_key.id,model=body.model,provider=provider.name,
                           usage=response_data.get("usage") or {},
                )

        try:
            await set_cached_response(redis_client, cache_key, response_data)

        except Exception as e:
            print(f"Error occurred while caching response: {e}")

        return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})

            
        


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



