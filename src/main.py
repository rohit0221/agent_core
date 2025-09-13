from fastapi import FastAPI, Request
from typing import Any, Dict, List
import os, json, re
import urllib.parse
import urllib.request

app = FastAPI()

# === Config ===
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")  # your MCP server base

def http_get_json(url: str) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Return a structured error so the endpoint never crashes
        return {"_error": f"HTTP call failed: {type(e).__name__}: {e}", "_url": url}

def call_order_lookup(order_id: str) -> Dict[str, Any]:
    q = urllib.parse.urlencode({"order_id": order_id})
    url = f"{MCP_BASE_URL}/debug/order_lookup?{q}"
    return http_get_json(url)

def call_kb_search(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    q = urllib.parse.urlencode({"query": query, "top_k": str(top_k)})
    url = f"{MCP_BASE_URL}/debug/kb_search?{q}"
    return http_get_json(url)

def route_to_tool(prompt: str) -> Dict[str, Any]:
    p = prompt.strip()

    # order lookup: "order 12345" or "order: 12345"
    m = re.search(r"\border[:\s]+(\d{3,})\b", p, re.IGNORECASE)
    if m:
        order_id = m.group(1)
        data = call_order_lookup(order_id)
        return {"tool": "order_lookup", "args": {"order_id": order_id}, "result": data}

    # kb search: "kb search refund" or "search refund"
    m = re.search(r"\b(?:kb\s+search|search)\s+(.+)", p, re.IGNORECASE)
    if m:
        query = m.group(1).strip()
        data = call_kb_search(query)
        return {"tool": "kb_search", "args": {"query": query, "top_k": 3}, "result": data}

    return {"tool": None}

@app.get("/ping")
async def ping():
    return {"status": "healthy", "mcp_base_url": MCP_BASE_URL}

@app.post("/invocations")
async def invocations(request: Request):
    body: Dict[str, Any] = await request.json()
    prompt = (
        body.get("prompt") or body.get("input") or body.get("message") or body.get("inputText")
    )
    if not prompt:
        return {"response": "Say: 'order 12345' or 'search refund policy'.", "status": "success"}

    routed = route_to_tool(prompt)

    if routed["tool"] == "order_lookup":
        result = routed["result"]
        if isinstance(result, dict) and result.get("_error"):
            return {"response": f"Tool error: {result['_error']}", "tool_call": routed, "status": "error"}
        if "error" in result:
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

    # fallback
    return {"response": f"You said: {prompt}", "status": "success"}
