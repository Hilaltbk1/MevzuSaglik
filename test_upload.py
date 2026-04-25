import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API anahtarı
api_key = os.getenv("TENANT_API_KEY", "ecea57ae955f01e1c22000559d761a8d4cb8df0c7ed7fc2d7659e536bcb75317")
base_url = "http://localhost:8000"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# Önce session oluşturalım (gerekli mi kontrol et)
session_data = {
    "user_name": "test_user"
}

print("Session oluşturuluyor...")
try:
    response = requests.post(f"{base_url}/sessions/create", json=session_data, headers=headers)
    print(f"Session response: {response.status_code}")
    if response.status_code == 200:
        print(f"Session: {response.json()}")
except Exception as e:
    print(f"Session hatası: {e}")

# Şimdi belge yüklemeyi test edelim
print("\nBelge yükleme testi...")

# Test için küçük bir PDF dosyası oluşturalım (veya mevcut bir dosya kullanalım)
test_files = []

# Eğer test dosyası yoksa oluşturalım
import tempfile
import base64

# Basit bir PDF içeriği oluşturalım (base64 encoded)
simple_pdf = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000053 00000 n
0000000102 00000 n
0000000151 00000 n
0000000222 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
281
%%EOF"""

# Base64 encode
pdf_bytes = simple_pdf.encode('utf-8')
pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

upload_data = {
    "files": [
        {
            "filename": "test_document.pdf",
            "content": pdf_base64
        }
    ]
}

print(f"Upload data hazır: {len(upload_data['files'])} dosya")

try:
    response = requests.post(f"{base_url}/add_documents/add", json=upload_data, headers=headers)
    print(f"Upload response status: {response.status_code}")
    print(f"Upload response: {response.json()}")
except Exception as e:
    print(f"Upload hatası: {e}")
    
    # Daha basit bir test - sadece endpoint'in çalışıp çalışmadığını kontrol edelim
    print("\nEndpoint kontrolü...")
    try:
        test_response = requests.get(f"{base_url}/health")
        print(f"Health check: {test_response.status_code}")
        print(f"Health response: {test_response.text[:100]}")
    except Exception as e2:
        print(f"Health check hatası: {e2}")