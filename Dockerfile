FROM python:3.11-slim

WORKDIR /app

# 1. Pip'i güncelle
RUN pip install --upgrade pip

# 2. Gereksinimleri DOSYADAN DEĞİL, direkt komutla kuruyoruz (Çakışmayı böyle aşacağız)
RUN pip install --no-cache-dir \
    langchain==0.2.17 \
    langchain-community==0.2.19 \
    langchain-core==0.2.43 \
    langchain-google-genai==1.0.10 \
    langchain-qdrant==0.1.2 \
    langgraph==0.2.76 \
    sqlalchemy==2.0.31 \
    pymysql==1.1.1 \
    python-dotenv==1.0.1 \
    uvicorn==0.30.1 \
    fastapi==0.111.0 \
    cryptography==46.0.5

# 3. Proje dosyalarını kopyala
COPY . .

# 4. Klasör yapısı ve Port ayarları
ENV PYTHONPATH="/app/backend"
ENV PORT=10000

# 5. Uygulamayı başlat
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]