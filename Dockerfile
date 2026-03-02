FROM python:3.11-slim

WORKDIR /app

# Requirements'ı kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ÖNEMLİ: Tüm dosyaları bir 'backend' klasörü içine kopyalıyoruz
COPY backend ./backend/

# Uvicorn'u bu yeni yapıya göre başlatıyoruz
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]