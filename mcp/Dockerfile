FROM --platform=linux/arm64 python:3.11-slim

# Work from /app/mcp so the script path is simple
WORKDIR /app/mcp

# Install deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy server code
COPY . .

EXPOSE 8000
CMD ["python", "my_mcp_server.py"]
