# 1. Aşama: Temel imaj
FROM python:3.11-slim

# 2. Aşama: Çalışma dizini
WORKDIR /app

# 3. Aşama: Gerekli sistem araçlarını kur (Bazen derleme için gerekebilir)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Aşama: Önce pip'i güncelle
RUN pip install --upgrade pip

# 5. Aşama: Paketleri TEK BİR komutta kur (Bağımlılıkları daha iyi yönetir)
RUN pip install --no-cache-dir \
    "protobuf==4.25.3" \
    "pydantic>=2.9.0" \
    "uvicorn[standard]" \
    fastapi \
    langchain==0.2.17 \
    langchain-community==0.2.19 \
    langchain-google-genai==1.0.10 \
    langchain-qdrant \
    google-generativeai==0.7.2 \
    pymysql \
    cryptography \
    sqlalchemy \
    python-dotenv

# 6. Aşama: Proje dosyalarını kopyala
COPY . .

# 7. Aşama: Uygulamayı başlat (Tam yol kullanarak uvicorn'u çağır)
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]