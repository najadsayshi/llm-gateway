from fastapi import FastAPI

app = FastAPI(title="LLM Gateway")



@app.get("/health")
async def health():
    return {"status": "ok"}
