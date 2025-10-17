FROM python:3.11.9-slim-bookworm

WORKDIR /app
COPY requirements.txt .

# 1. 先裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# 2. 強制只用 wheel（不編譯 greenlet）
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt && \
    playwright install chromium

COPY main.py .
CMD ["python", "main.py"]