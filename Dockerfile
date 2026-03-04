FROM python:3.11-slim

WORKDIR /app

# 1. Pip'i güncelle
RUN pip install --upgrade pip

# 2. Gerekli Python paketlerini kur (versiyon sabitlemeden)
RUN pip install --no-cache-dir \
    langchain \
    langchain-community \
    langchain-core \
    langchain-google-genai \
    langchain-qdrant \
    langgraph \
    google-generativeai \
    sqlalchemy \
    pymysql \
    python-dotenv \
    uvicorn \
    fastapi \
    cryptography

# 3. Proje dosyalarını kopyala
COPY . .

# 4. PYTHONPATH ve PORT
ENV PYTHONPATH="/app"

# Render PORT değişkenini kendisi veriyor, yoksa 8000 kullan
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]