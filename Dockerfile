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
    "pydantic>=2.9.0,<3" \
    langchain==0.2.17 \
    langchain-community==0.2.19 \
    langchain-core==0.2.43 \
    langchain-google-genai==1.0.10 \
    langchain-qdrant==0.1.2 \
    langgraph==0.2.76 \
    google-generativeai==0.7.2 \     # ← 0.8.3 yerine 0.7.2 koy (1.0.10 ile uyumlu)
    sqlalchemy==2.0.31 \
    pymysql==1.1.1 \
    python-dotenv==1.0.1 \
    uvicorn==0.30.1 \
    fastapi==0.111.0 \
    cryptography

# 6. Aşama: Proje dosyalarını kopyala
COPY . .

# 7. Aşama: Uygulamayı başlat (Tam yol kullanarak uvicorn'u çağır)
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]