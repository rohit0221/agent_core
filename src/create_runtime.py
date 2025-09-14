# create_http_agent_runtime.py
import boto3, json, os
from botocore.exceptions import ClientError

REGION = os.getenv("AWS_REGION", "us-east-1")
ACCOUNT_ID = "175573404892"
ROLE_ARN = "arn:aws:iam::175573404892:role/AgentCoreRuntimeRole"

ECR_REPO = "agentcore-poc"
IMAGE_TAG = "v9"   # <-- your agent image tag
IMAGE_URI = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPO}:{IMAGE_TAG}"

# paste your MCP runtime ARN here
MCP_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:175573404892:runtime/mcpserverruntimepoc-Ut1HpNAffX"

RUNTIME_NAME = "agentcorepoc"  # [A-Za-z][A-Za-z0-9_]{0,47}

client = boto3.client("bedrock-agentcore-control", region_name=REGION)

payload = {
    "agentRuntimeName": RUNTIME_NAME,
    "agentRuntimeArtifact": {
        "containerConfiguration": {"containerUri": IMAGE_URI}
    },
    "roleArn": ROLE_ARN,
    "networkConfiguration": {"networkMode": "PUBLIC"},
    "protocolConfiguration": {"serverProtocol": "HTTP"},
    # IMPORTANT: use environmentVariables (plural)
    "environmentVariables": {
        "MCP_RUNTIME_ARN": MCP_RUNTIME_ARN,
        "IMAGE_TAG": IMAGE_TAG
    },
}

try:
    resp = client.create_agent_runtime(**payload)
    print("RAW RESPONSE:\n", json.dumps(resp, indent=2, default=str))
    arn = (
        resp.get("agentRuntime", {}).get("agentRuntimeArn")
        or resp.get("agentRuntimeArn")
        or resp.get("arn")
        or resp.get("agentRuntimeSummary", {}).get("agentRuntimeArn")
    )
    if not arn:
        raise RuntimeError("Could not find agent runtime ARN in response.")
    print("\nCreated HTTP AgentRuntime ARN:", arn)
except ClientError as e:
    print("CreateAgentRuntime failed:", json.dumps(e.response.get("Error", {}), indent=2))
    raise
