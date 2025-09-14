# mcp/invoke_mcp_directly.py  (FINAL)
import boto3, json, uuid

REGION = "us-east-1"
MCP_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:175573404892:runtime/mcpserverruntimepoc-dGKwFjDxdL"

ac = boto3.client("bedrock-agentcore", region_name=REGION)

def call_mcp(jsonrpc_message: dict, session_id: str | None):
    kwargs = {
        "agentRuntimeArn": MCP_RUNTIME_ARN,
        "contentType": "application/json",
        "accept": "application/json",
        "payload": json.dumps(jsonrpc_message).encode("utf-8"),
    }
    if session_id:
        kwargs["runtimeSessionId"] = session_id

    resp = ac.invoke_agent_runtime(**kwargs)
    sid = resp.get("runtimeSessionId")
    body = resp["response"].read().decode("utf-8") or ""
    return sid, (json.loads(body) if body and body.strip().startswith("{") else body)

def main():
    sid = None

    # 1) initialize (JSON-RPC)
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"client": "agentcore-poc", "capabilities": {"tools": True}},
    }
    sid, out = call_mcp(init, sid)
    print("initialize →", json.dumps(out, indent=2))

    # 2) list tools (optional sanity check)
    lst = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    sid, out = call_mcp(lst, sid)
    print("tools/list →", json.dumps(out, indent=2))

    # 3) tools/call: order_lookup
    order = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "order_lookup", "arguments": {"order_id": "12345"}},
    }
    sid, out = call_mcp(order, sid)
    print("tools/call(order_lookup) →", json.dumps(out, indent=2))

    # 4) tools/call: kb_search
    kb = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "kb_search", "arguments": {"query": "refund", "top_k": 3}},
    }
    sid, out = call_mcp(kb, sid)
    print("tools/call(kb_search) →", json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
