FROM --platform=linux/arm64 python:3.11-slim
WORKDIR /app/src

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app
COPY . .

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
