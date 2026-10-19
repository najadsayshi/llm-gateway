import httpx


async def chat_completion(client: httpx.AsyncClient, payload: dict) -> httpx.Response:
    return await client.post("/chat/completions", json=payload)


async def open_chat_stream(client: httpx.AsyncClient, payload: dict) -> httpx.Response:
    request = client.build_request("POST", "/chat/completions", json=payload)
    return await client.send(request, stream=True)
