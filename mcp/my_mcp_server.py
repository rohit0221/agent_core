# mcp/my_mcp_server.py
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# --- sample data ---
ORDERS = {
    "12345": {"order_id": "12345", "status": "Shipped", "eta": "2025-09-20", "items": 3, "total": 129.50},
    "55555": {"order_id": "55555", "status": "Processing", "eta": "2025-09-17", "items": 1, "total": 19.99},
}
FAQ = [
    {"title": "Return policy", "snippet": "You can return items within 30 days with receipt."},
    {"title": "Shipping delays", "snippet": "Delays may occur during holidays or extreme weather."},
    {"title": "Refund timeline", "snippet": "Refunds usually take 5–7 business days to appear."},
]

# --- tool funcs ---
def order_lookup(order_id: str) -> Dict[str, Any]:
    return ORDERS.get(order_id, {"error": "Order not found", "order_id": order_id})

def kb_search(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    q = query.lower()
    results = [f for f in FAQ if q in f["title"].lower() or q in f["snippet"].lower()]
    return results[: int(top_k)]

# --- schemas for tools/list ---
TOOLS = {
    "order_lookup": {
        "func": order_lookup,
        "schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "description": "Lookup order status/details by order_id.",
    },
    "kb_search": {
        "func": kb_search,
        "schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "description": "Search FAQ snippets. Returns top_k matches.",
    },
}

# --- json-rpc wrapper ---
class JsonRpc(BaseModel):
    jsonrpc: str
    id: Any | None = None
    method: str
    params: Dict[str, Any] | None = None

@app.post("/mcp")
def mcp_endpoint(req: JsonRpc):
    try:
        if req.jsonrpc != "2.0":
            raise ValueError("invalid jsonrpc version")

        if req.method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": {
                    "tools": [
                        {"name": name, "description": meta["description"], "input_schema": meta["schema"]}
                        for name, meta in TOOLS.items()
                    ]
                },
            }

        if req.method == "tools/call":
            name = req.params.get("name")
            args = req.params.get("arguments", {})
            if name not in TOOLS:
                raise ValueError(f"unknown tool: {name}")
            func = TOOLS[name]["func"]
            result = func(**args)
            return {"jsonrpc": "2.0", "id": req.id, "result": {"content": result}}

        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32601, "message": f"method not found: {req.method}"}}

    except Exception as e:
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32603, "message": f"internal error: {e}"}}

# --- debug routes (optional) ---
@app.get("/ping")
def ping():
    return {"status": "ok", "service": "mcp-server"}

@app.get("/debug/order_lookup")
def debug_order_lookup(order_id: str):
    return JSONResponse(order_lookup(order_id))

@app.get("/debug/kb_search")
def debug_kb_search(query: str, top_k: int = 3):
    return JSONResponse(kb_search(query, top_k))

if __name__ == "__main__":
    import uvicorn
    # IMPORTANT: 8080 (not 8000)
    uvicorn.run(app, host="0.0.0.0", port=8080)
