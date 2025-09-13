# Create Repo:
aws ecr create-repository --repository-name agentcore-poc --region us-east-1

# Login to CLI:
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 175573404892.dkr.ecr.us-east-1.amazonaws.com

# optional: set up buildx once
docker buildx create --use

# build for ARM64
docker buildx build --platform linux/arm64 -t agentcore-poc:arm64 --load .

# run the container locally
docker run --platform linux/arm64 -p 8080:8080 agentcore-poc:arm64

docker tag agentcore-poc:arm64 175573404892.dkr.ecr.us-east-1.amazonaws.com/agentcore-poc:latest

docker push 175573404892.dkr.ecr.us-east-1.amazonaws.com/agentcore-poc:latest


# Local test
curl http://localhost:8080/ping


curl -X POST http://localhost:8080/invocations ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"hello\"}"
