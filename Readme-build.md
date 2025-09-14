# same account & region for both
export REGION=us-east-1
export ACCOUNT=175573404892

# Docker Login
aws ecr get-login-password --region $REGION \
| docker login --username AWS --password-stdin ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com


# ---------- ensure repos exist ----------
aws ecr describe-repositories --repository-names agentcore-poc --region $REGION >/dev/null 2>&1 \
 || aws ecr create-repository --repository-name agentcore-poc --region $REGION

aws ecr describe-repositories --repository-names mcp-server --region $REGION >/dev/null 2>&1 \
 || aws ecr create-repository --repository-name mcp-server --region $REGION

# ---------- buildx once ----------
docker buildx create --use || true

# agent image repo + tag
export AGENT_REPO=agentcore-poc
export AGENT_TAG=v9
export AGENT_IMAGE=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${AGENT_REPO}:${AGENT_TAG}

# mcp image repo + tag
export MCP_REPO=mcp-server
export MCP_TAG=v13
export MCP_IMAGE=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${MCP_REPO}:${MCP_TAG}

# Agent (src)
docker buildx build --platform linux/arm64 -f src/Dockerfile -t ${AGENT_REPO}:${AGENT_TAG} ./src --load
docker tag ${AGENT_REPO}:${AGENT_TAG} ${AGENT_IMAGE}
docker push ${AGENT_IMAGE}


# MCP (mcp)
docker buildx build --platform linux/arm64 -f mcp/Dockerfile -t ${MCP_REPO}:${MCP_TAG} ./mcp --load
docker tag ${MCP_REPO}:${MCP_TAG} ${MCP_IMAGE}
docker push ${MCP_IMAGE}



# starting the containers locally:

# Create a local bridge network (so agent can reach MCP by name)
docker network create agentcore-net || true


# Start the MCP container (port 8000)
export REGION=us-east-1
export ACCOUNT=175573404892
export MCP_REPO=mcp-server
export MCP_TAG=v9
export MCP_IMAGE=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${MCP_REPO}:${MCP_TAG}
docker run -d --name mcp --network agentcore-net -p 8000:8000 ${MCP_IMAGE}


export REGION=us-east-1
export ACCOUNT=175573404892
export AGENT_REPO=agentcore-poc
export AGENT_TAG=v9
export AGENT_IMAGE=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${AGENT_REPO}:${AGENT_TAG}

docker run -d --name agent --network agentcore-net -p 8080:8080 \
  -e MCP_BASE_URL="http://mcp:8000" \
  ${AGENT_IMAGE}


# verify 

## MCP:
curl http://localhost:8000/ping
curl "http://localhost:8000/debug/order_lookup?order_id=12345"
curl "http://localhost:8000/debug/kb_search?query=refund"


## Agent
curl http://localhost:8080/ping


## End-to-End:

curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d "{\"prompt\":\"order 12345\"}"
curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d "{\"prompt\":\"search refund\"}"
