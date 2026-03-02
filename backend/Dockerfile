FROM python:3.11-slim

WORKDIR /app

# Requirements'ı kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# TÜM PROJEYİ kopyala (backend klasörüyle birlikte gelsin)
COPY . .

# Başlatma komutunu değiştir:
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]