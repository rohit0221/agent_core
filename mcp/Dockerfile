FROM --platform=linux/arm64 python:3.11-slim
WORKDIR /app/mcp

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app
COPY . .

EXPOSE 8000
CMD ["python", "my_mcp_server.py"]
