# invoke_agent_tools.py
import boto3, json, sys

REGION = "us-east-1"
AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:175573404892:runtime/agentcorepoc-X18bBsAb4Q"

client = boto3.client("bedrock-agentcore", region_name=REGION)

def call_agent(prompt: str, session_id: str | None) -> tuple[str, dict]:
    kwargs = dict(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        contentType="application/json",
        accept="application/json",
        payload=json.dumps({"prompt": prompt}).encode("utf-8"),
    )
    if session_id:
        kwargs["runtimeSessionId"] = session_id

    resp = client.invoke_agent_runtime(**kwargs)
    sid = resp.get("runtimeSessionId")
    body_text = resp["response"].read().decode("utf-8")  # streaming body
    try:
        body = json.loads(body_text)
    except Exception:
        body = {"raw": body_text}
    return sid, body

def main():
    session_id = None
    prompts = [
        "order 12345",      # should hit MCP tool: order_lookup
        "search refund",    # should hit MCP tool: kb_search
    ]

    for i, p in enumerate(prompts, start=1):
        session_id, body = call_agent(p, session_id)
        print(f"\n--- Turn {i} ---")
        print("Session:", session_id)
        print("Prompt :", p)
        print("Reply  :", json.dumps(body, indent=2))

if __name__ == "__main__":
    main()
