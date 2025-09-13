# ARM64 base for AgentCore
FROM --platform=linux/arm64 python:3.11-slim

# Work from /app/src so "main:app" works
WORKDIR /app/src

# Install deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app code (everything in src/)
COPY . .

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
