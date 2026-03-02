FROM python:3.11-slim

# ... (üstteki sistem paketleri kısmı aynı kalsın) ...

WORKDIR /app

# DOĞRU SATIR BU OLMALI:
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# BU SATIRI DA ŞÖYLE DÜZELT:
COPY . .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]