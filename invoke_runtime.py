import boto3, json

REGION = "us-east-1"
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:175573404892:runtime/agentcorepoc-b13QXTGPL2"

client = boto3.client("bedrock-agentcore", region_name=REGION)

resp = client.invoke_agent_runtime(
    agentRuntimeArn=RUNTIME_ARN,
    contentType="application/json",
    accept="application/json",
    payload=json.dumps({"inputText": "hello from agentcore"}).encode("utf-8")
)

print("STATUS:", resp.get("statusCode"))
print("SESSION:", resp.get("runtimeSessionId"))

# Read the streaming body
body_bytes = resp["response"].read()
body_text = body_bytes.decode("utf-8")
print("BODY RAW:", body_text)

# Try to parse JSON if it’s JSON
try:
    parsed = json.loads(body_text)
    print("BODY PARSED:", json.dumps(parsed, indent=2))
except Exception:
    print("BODY is not JSON")
