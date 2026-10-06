
import httpx

async def chat_completion(client,payload):

    response =await client.post("/chat/completions",json=payload)
    return response
