FROM python:3.11-slim

WORKDIR /app

# 1. Önce requirements'ı kopyalayıp kütüphaneleri kuruyoruz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. PROJENİN TAMAMINI kopyalıyoruz (backend klasörüyle birlikte)
COPY . .

# 3. Python'a /app dizinini ana yol olarak tanıtıyoruz (Import hatalarını önler)
ENV PYTHONPATH=/app

# 4. Uygulamayı başlatıyoruz
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]