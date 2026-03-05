FROM python:3.11-slim

WORKDIR /app

# 1. Pip'i güncelle
# Bu satır değiştiği için Docker altındaki tüm paketleri yeniden yükler
# Önce bu ikiliyi kurmak kritik
RUN pip install --no-cache-dir "protobuf==4.25.3" "pydantic>=2.9.0"

# Sonra diğerlerini ekle
RUN pip install --no-cache-dir \
    langchain==0.2.17 \
    langchain-community==0.2.19 \
    langchain-google-genai==1.0.10 \
    langchain-qdrant \
    google-generativeai==0.7.2 \
    pymysql \
    cryptography \
    sqlalchemy


# 5. Proje dosyalarını kopyala
COPY . .

ENV PYTHONPATH="/app"

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]