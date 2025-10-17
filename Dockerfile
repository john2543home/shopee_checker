FROM python:3.11.9-slim-bookworm

# 1. 先裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# 2. 先裝 greenlet  wheel（不編譯）
RUN pip install --no-cache-dir --only-binary=:all: greenlet

# 3. 再裝其他套件
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

COPY main.py .
CMD ["python", "main.py"]