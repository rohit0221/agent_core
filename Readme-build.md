# same account & region for both
export REGION=us-east-1
export ACCOUNT=175573404892

# agent image repo + tag
export AGENT_REPO=agentcore-poc
export AGENT_TAG=vv
export AGENT_IMAGE=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${AGENT_REPO}:${AGENT_TAG}

# mcp image repo + tag
export MCP_REPO=mcp-server
export MCP_TAG=v1
export MCP_IMAGE=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${MCP_REPO}:${MCP_TAG}


aws ecr get-login-password --region $REGION \
| docker login --username AWS --password-stdin ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com
