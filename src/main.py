from fastapi import FastAPI, Request
from typing import Any, Dict

app = FastAPI()
CALL_COUNT = 0  # process-scoped counter to prove session stickiness

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

@app.post("/invocations")
async def invocations(request: Request):
    global CALL_COUNT
    CALL_COUNT += 1
    body: Dict[str, Any] = await request.json()
    prompt = (
        body.get("prompt")
        or body.get("input")
        or body.get("message")
        or body.get("inputText")   # accept your previous key too
    )
    reply = (
        f"[call #{CALL_COUNT}] You said: {prompt}"
        if prompt
        else f"[call #{CALL_COUNT}] Hello from AgentCore POC!"
    )
    return {"response": reply, "status": "success"}
