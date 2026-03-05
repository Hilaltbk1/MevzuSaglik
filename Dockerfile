# 1. Aşama: Python 3.12 Kullan (Hatanın tek çözümü budur)
FROM python:3.12-slim

# 2. Aşama: Çalışma dizini
WORKDIR /app

# 3. Aşama: Gerekli sistem araçlarını kur
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 4. Aşama: Paketleri kur (Versiyonlar 3.12 ile uyumlu hale getirildi)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir \
    "pydantic>=2.9.0" \
    "protobuf==5.26.1" \
    "grpcio==1.62.1" \
    "qdrant-client==1.12.1" \
    "google-generativeai==0.7.2" \
    "langchain==0.2.17" \
    "langchain-community==0.2.19" \
    "langchain-google-genai==1.0.10" \
    "langchain-qdrant==0.2.1" \
    "sqlalchemy==2.0.31" \
    "pymysql==1.1.1" \
    "python-dotenv==1.0.1" \
    "uvicorn==0.30.1" \
    "fastapi==0.111.0" \
    "cryptography==46.0.5" \
    "rank_bm25"

# 5. Aşama: Proje dosyalarını kopyala
COPY . .

# 6. Aşama: Başlatma (Hatalı importları önlemek için modül olarak başlatıyoruz)
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]