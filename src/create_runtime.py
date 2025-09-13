import boto3, json
from botocore.exceptions import ClientError

REGION = "us-east-1"
IMAGE_URI = "175573404892.dkr.ecr.us-east-1.amazonaws.com/agentcore-poc:v1"
ROLE_ARN = "arn:aws:iam::175573404892:role/AgentCoreRuntimeRole"

client = boto3.client("bedrock-agentcore-control", region_name=REGION)

payload = {
    "agentRuntimeName": "agentcorepoc",
    "agentRuntimeArtifact": {"containerConfiguration": {"containerUri": IMAGE_URI}},
    "roleArn": ROLE_ARN,
    "networkConfiguration": {"networkMode": "PUBLIC"},
    "protocolConfiguration": {"serverProtocol": "HTTP"},
}

try:
    resp = client.create_agent_runtime(**payload)

    # Show the raw response to confirm the precise shape
    print("RAW RESPONSE:\n", json.dumps(resp, indent=2, default=str))

    # Try common locations for the ARN
    arn = (
        resp.get("agentRuntime", {}).get("agentRuntimeArn")
        or resp.get("agentRuntimeArn")
        or resp.get("arn")
        or resp.get("agentRuntimeSummary", {}).get("agentRuntimeArn")
    )

    if not arn:
        raise RuntimeError("Could not find agent runtime ARN in response. See RAW RESPONSE above.")

    print("\nCreated AgentRuntime ARN:", arn)

except ClientError as e:
    print("CreateAgentRuntime failed:", json.dumps(e.response.get("Error", {}), indent=2))
    raise
