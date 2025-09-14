from fastapi import FastAPI, Request
from typing import Any, Dict, List, Optional
import os, json, re, uuid, urllib.parse, urllib.request
import boto3
from botocore.exceptions import ClientError, BotoCoreError

app = FastAPI()

# === Config ===
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
MCP_RUNTIME_ARN = os.getenv("MCP_RUNTIME_ARN")  # <-- set in AWS runtime env
if not MCP_RUNTIME_ARN:
    MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")  # local dev
else:
    MCP_BASE_URL = None

# Data-plane client (only used if MCP_RUNTIME_ARN is set)
_bedrock_client = None
def _client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)
    return _bedrock_client

# Keep a single MCP session per process
_mcp_session_id: Optional[str] = None

# -------- True MCP calls via AgentCore data plane --------
def _mcp_invoke(message: Dict[str, Any]) -> Dict[str, Any]:
    global _mcp_session_id
    kwargs = dict(
        agentRuntimeArn=MCP_RUNTIME_ARN,
        contentType="application/json",
        accept="application/json",
        payload=json.dumps(message).encode("utf-8"),
    )
    if _mcp_session_id:
        kwargs["runtimeSessionId"] = _mcp_session_id

    resp = _client().invoke_agent_runtime(**kwargs)
    sid = resp.get("runtimeSessionId")
    if sid:
        _mcp_session_id = sid

    body_text = resp["response"].read().decode("utf-8")
    try:
        return json.loads(body_text)
    except Exception:
        return {"_raw": body_text}

def _mcp_call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    req = {
        "type": "mcp.tool.call",
        "id": str(uuid.uuid4()),
        "tool": tool_name,
        "arguments": arguments,
    }
    try:
        out = _mcp_invoke(req)
        if isinstance(out, dict):
            if "result" in out:
                return out["result"]
            if "error" in out:
                return {"_error": f"MCP error: {out['error']}"}
            if "data" in out:
                return out["data"]
            if "outputs" in out:
                return out["outputs"]
            return {"_error": f"Unexpected MCP response: {json.dumps(out)[:300]}"}
        return {"_error": f"Non-JSON MCP response: {str(out)[:300]}"}
    except (ClientError, BotoCoreError) as e:
        return {"_error": f"MCP invoke failed: {type(e).__name__}: {e}"}

# -------- Tool wrappers --------
def call_order_lookup(order_id: str) -> Dict[str, Any]:
    if MCP_RUNTIME_ARN:
        return _mcp_call_tool("order_lookup", {"order_id": order_id})
    # local HTTP fallback
    q = urllib.parse.urlencode({"order_id": order_id})
    url = f"{MCP_BASE_URL}/debug/order_lookup?{q}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": f"HTTP call failed: {type(e).__name__}: {e}", "_url": url}

def call_kb_search(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    if MCP_RUNTIME_ARN:
        out = _mcp_call_tool("kb_search", {"query": query, "top_k": top_k})
        if isinstance(out, dict) and out.get("_error"):
            return out
        return out if isinstance(out, list) else [out]
    # local HTTP fallback
    q = urllib.parse.urlencode({"query": query, "top_k": str(top_k)})
    url = f"{MCP_BASE_URL}/debug/kb_search?{q}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": f"HTTP call failed: {type(e).__name__}: {e}", "_url": url}

# -------- Routing --------
def route_to_tool(prompt: str) -> Dict[str, Any]:
    p = prompt.strip()

    m = re.search(r"\border[:\s]+(\d{3,})\b", p, re.IGNORECASE)
    if m:
        order_id = m.group(1)
        data = call_order_lookup(order_id)
        return {"tool": "order_lookup", "args": {"order_id": order_id}, "result": data}

    m = re.search(r"\b(?:kb\s+search|search)\s+(.+)", p, re.IGNORECASE)
    if m:
        query = m.group(1).strip()
        data = call_kb_search(query)
        return {"tool": "kb_search", "args": {"query": query, "top_k": 3}, "result": data}

    return {"tool": None}

# -------- API surface --------
@app.get("/ping")
async def ping():
    return {
        "status": "healthy",
        "mode": "MCP" if MCP_RUNTIME_ARN else "HTTP-DEBUG",
        "mcp_runtime_arn": MCP_RUNTIME_ARN,
        "region": AWS_REGION,
    }

@app.post("/invocations")
async def invocations(request: Request):
    body: Dict[str, Any] = await request.json()
    prompt = body.get("prompt") or body.get("input") or body.get("message") or body.get("inputText")
    if not prompt:
        return {"response": "Say: 'order 12345' or 'search refund policy'.", "status": "success"}

    routed = route_to_tool(prompt)

    if routed["tool"] == "order_lookup":
        result = routed["result"]
        if isinstance(result, dict) and result.get("_error"):
            return {"response": f"Tool error: {result['_error']}", "tool_call": routed, "status": "error"}
        if isinstance(result, dict) and "error" in result:
            reply = f"Order {routed['args']['order_id']} not found."
        else:
            reply = (
                f"Order {result['order_id']}: status {result['status']}, "
                f"ETA {result['eta']}, items {result['items']}, total {result['total']}"
            )
        return {"response": reply, "tool_call": routed, "status": "success"}

    if routed["tool"] == "kb_search":
        hits = routed["result"]
        if isinstance(hits, dict) and hits.get("_error"):
            return {"response": f"Tool error: {hits['_error']}", "tool_call": routed, "status": "error"}
        if not hits:
            reply = f"No FAQ hits for '{routed['args']['query']}'."
        else:
            bullets = "\n".join([f"- {h['title']}: {h['snippet']}" for h in hits])
            reply = f"Top matches for '{routed['args']['query']}':\n{bullets}"
        return {"response": reply, "tool_call": routed, "status": "success"}

    return {"response": f"You said: {prompt}", "status": "success"}
