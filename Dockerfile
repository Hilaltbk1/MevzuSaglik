# Python 3.12 slim (hafif ve hızlı)
FROM python:3.12-slim

# Çalışma dizini
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Pip güncelle
RUN pip install --no-cache-dir --upgrade pip

# requirements.txt kur
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install langchain-core explicitly (in case of dependency issues)
RUN pip install --no-cache-dir langchain-core>=0.1.0

# Tüm proje dosyalarını kopyala
COPY . .

# Uygulamayı başlat (uvicorn backend.main'i çalıştırır)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]