# Python 3.12 slim (hafif ve hızlı)
FROM python:3.12-slim

# Çalışma dizini
WORKDIR /app


# Pip güncelle
RUN pip install --no-cache-dir --upgrade pip

# requirements.txt kur
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını kopyala
COPY . .

# Uygulamayı başlat (uvicorn backend'i çalıştırır, Gradio'yu da aynı anda mount edebilirsin)
# Eğer Gradio'yu ayrı başlatmak istiyorsan aşağıdakini kullan
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]