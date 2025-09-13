# ARM64 base image
FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# If you’re using src/ layout, copy the project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
# (or COPY main.py . if you kept it at root)

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
