# create_mcp_runtime.py
import boto3, json, os
from botocore.exceptions import ClientError

REGION = os.getenv("AWS_REGION", "us-east-1")
ACCOUNT_ID = "175573404892"
ROLE_ARN = "arn:aws:iam::175573404892:role/AgentCoreRuntimeRole"

ECR_REPO = "mcp-server"
IMAGE_TAG = "v13"
IMAGE_URI = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPO}:{IMAGE_TAG}"

RUNTIME_NAME = "mcpserverruntimepoc"

client = boto3.client("bedrock-agentcore-control", region_name=REGION)

payload = {
    "agentRuntimeName": RUNTIME_NAME,
    "agentRuntimeArtifact": {"containerConfiguration": {"containerUri": IMAGE_URI}},
    "roleArn": ROLE_ARN,
    "networkConfiguration": {"networkMode": "PUBLIC"},
    "protocolConfiguration": {"serverProtocol": "MCP"},
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
    print("\nCreated MCP AgentRuntime ARN:", arn)
except ClientError as e:
    print("CreateAgentRuntime failed:", json.dumps(e.response.get("Error", {}), indent=2))
    raise
