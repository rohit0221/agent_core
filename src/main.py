from fastapi import FastAPI, Request
from typing import Any, Dict

app = FastAPI()

@app.get("/ping")
async def ping():
    # Health endpoint required by AgentCore
    return {"status": "healthy"}  # 200 means healthy

@app.post("/invocations")
async def invocations(request: Request):
    body: Dict[str, Any] = await request.json()
    # Very basic echo logic for the POC
    prompt = body.get("prompt") or body.get("input") or body.get("message")
    reply = f"You said: {prompt}" if prompt else "Hello from AgentCore POC!"
    return {"response": reply, "status": "success"}
