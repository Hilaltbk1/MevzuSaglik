# 1. Aşama: Python 3.12 Kullan (Tip hatasını çözen tek sürüm)
FROM python:3.12-slim

# 2. Aşama: Çalışma dizini
WORKDIR /app

# 3. Aşama: Gerekli sistem araçlarını kur
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 4. Aşama: Pip güncelleme
RUN pip install --upgrade pip

RUN pip install --no-cache-dir \
    "pydantic>=2.0" \
    "fastapi" \
    "uvicorn" \
    "python-dotenv" \
    "sqlalchemy" \
    "pymysql" \
    "cryptography" \
    "rank_bm25" \
    "google-generativeai" \
    "langchain>=0.2.0" \
    "langchain-community" \
    "langchain-core" \
    "langchain-text-splitters" \
    "langchain-google-genai" \
    "langchain-qdrant" \
    "qdrant-client"\
    "jinja2"  #
# 6. Aşama: Proje dosyalarını kopyala
COPY . .

# 7. Aşama: Başlatma
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]