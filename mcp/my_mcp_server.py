# mcp/my_mcp_server.py
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Use the FastAPI server adapter from mcp[fastapi]

from mcp.server.fastmcp import FastMCP
app = FastAPI()
server = FastMCP(app)   # MCP is mounted on /mcp by this adapter

# --- Fake data stores ---
ORDERS = {
    "12345": {"order_id": "12345", "status": "Shipped", "eta": "2025-09-20", "items": 3, "total": 129.50},
    "55555": {"order_id": "55555", "status": "Processing", "eta": "2025-09-17", "items": 1, "total": 19.99},
}
FAQ = [
    {"title": "Return policy", "snippet": "You can return items within 30 days with receipt."},
    {"title": "Shipping delays", "snippet": "Delays may occur during holidays or extreme weather."},
    {"title": "Refund timeline", "snippet": "Refunds usually take 5–7 business days to appear."},
]

# --- MCP tools ---
@server.tool()
def order_lookup(order_id: str) -> Dict[str, Any]:
    """Look up an order by order_id."""
    return ORDERS.get(order_id, {"error": "Order not found", "order_id": order_id})

@server.tool()
def kb_search(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    """Search a tiny FAQ store."""
    q = query.lower()
    results = [f for f in FAQ if q in f["title"].lower() or q in f["snippet"].lower()]
    return results[:top_k]

# --- Local debug endpoints (plain FastAPI, optional) ---
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
    # MCP transport is exposed at /mcp; debug routes at /ping and /debug/*
    uvicorn.run(app, host="0.0.0.0", port=8000)
