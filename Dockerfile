FROM python:3.11-slim

WORKDIR /app

# 1. Pip'i güncelle
RUN pip install --no-cache-dir --upgrade pip

# 2. Önce en kritik bağımlılıkları ve tipleri kur (EnumTypeWrapper hatasını engeller)
RUN pip install --no-cache-dir \
    "pydantic>=2.9.0" \
    "google-auth>=2.47.0" \
    "protobuf==4.25.3"

# 3. Langchain paketlerini topluca kur
RUN pip install --no-cache-dir \
    langchain==0.2.17 \
    langchain-community==0.2.19 \
    langchain-core==0.2.43 \
    langchain-google-genai==1.0.10 \
    langchain-qdrant \
    langgraph \
    google-generativeai==0.7.2

# 4. Diğer kütüphaneler
RUN pip install --no-cache-dir \
    sqlalchemy \
    pymysql \
    python-dotenv \
    uvicorn \
    fastapi \
    cryptography

# 5. Proje dosyalarını kopyala
COPY . .

ENV PYTHONPATH="/app"

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]