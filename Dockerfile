# Örnek olması açısından:
FROM python:3.10-slim

WORKDIR /app

# ÖNCE requirements dosyasını kopyalayıp yüklemelisiniz
COPY requirements.txt .

# Önce pip'i güncelleyin, sonra paketleri kurun
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# SONRA geri kalan kodları kopyalamalısınız
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]