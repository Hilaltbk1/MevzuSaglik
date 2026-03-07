# Python 3.12 slim (hafif ve hızlı)
FROM python:3.12-slim

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıkları (minimumda tutuyoruz)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Pip güncelle
RUN pip install --no-cache-dir --upgrade pip

# Tüm bağımlılıkları kur (Gradio + backend paketleri)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    python-dotenv \
    sqlalchemy \
    pymysql \
    cryptography \
    rank_bm25 \
    google-generativeai \
    langchain>=0.2.0 \
    langchain-community \
    langchain-core \
    langchain-text-splitters \
    langchain-google-genai \
    langchain-qdrant \
    qdrant-client \
    jinja2 \
    pydantic>=2.0 \
    gradio>=4.44.0   # Gradio'yu ekledik!

# Önce requirements.txt varsa onu kur (cache avantajı için)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true  # yoksa hata vermesin

# Tüm proje dosyalarını kopyala
COPY . .

# Uygulamayı başlat (uvicorn backend'i çalıştırır, Gradio'yu da aynı anda mount edebilirsin)
# Eğer Gradio'yu ayrı başlatmak istiyorsan aşağıdakini kullan
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]