# 1. Aşama: Temel imaj
FROM python:3.11-slim

# 2. Aşama: Çalışma dizini
WORKDIR /app

# 3. Aşama: Gerekli sistem araçlarını kur (Bazen derleme için gerekebilir)
RUN apt-get update && apt-get install -y --no-install-recommends \
    dnsutils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 4. Aşama: Önce pip'i güncelle
RUN pip install --upgrade pip

# 5. Aşama: Paketleri TEK BİR komutta kur (Bağımlılıkları daha iyi yönetir)
RUN pip install --no-cache-dir \
    "protobuf==3.20.3" \
    "pydantic>=2.0" \
    "google-generativeai==0.5.4" \
    "langchain-google-genai==1.0.3" \
    "uvicorn[standard]" \
    "fastapi" \
    "langchain" \
    "langchain-community" \
    "langchain-qdrant" \
    "sqlalchemy" \
    "pymysql" \
    "cryptography" \
    "python-dotenv"

# 6. Aşama: Proje dosyalarını kopyala
COPY . .

# 7. Aşama: Uygulamayı başlat (Tam yol kullanarak uvicorn'u çağır)
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]