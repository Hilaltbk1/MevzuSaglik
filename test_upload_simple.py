import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

# API anahtarı
api_key = os.getenv("TENANT_API_KEY", "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af")
base_url = "http://127.0.0.1:8000"

headers = {
    "X-API-Key": api_key,
}

print(f"API Key: {api_key[:10]}...")
print(f"Base URL: {base_url}")

# Önce health endpoint'ini kontrol et
print("\n1. Health endpoint kontrolü...")
try:
    response = requests.get(f"{base_url}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   Health check hatası: {e}")

# Belge yükleme endpoint'ini test et
print("\n2. Belge yükleme endpoint kontrolü...")
try:
    # Önce endpoint'in varlığını kontrol et
    response = requests.get(f"{base_url}/add_documents/status/test", headers=headers, timeout=5)
    print(f"   Status endpoint test: {response.status_code}")
    if response.status_code == 404:
        print("   ✓ Endpoint mevcut (404 beklenen bir hata)")
    else:
        print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   Endpoint kontrol hatası: {e}")

# Şimdi gerçek bir belge yükleme testi yapalım
print("\n3. Gerçek belge yükleme testi...")

# Test için küçük bir text dosyası oluşturalım
test_file_content = b"This is a test document about health regulations."

# Multipart form data ile yükleme
files = {
    'files': ('test_document.txt', test_file_content, 'text/plain')
}

try:
    response = requests.post(
        f"{base_url}/add_documents/add",
        files=files,
        headers=headers,
        timeout=30
    )
    print(f"   Upload status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✓ Başarılı! Response: {response.json()}")
    else:
        print(f"   ✗ Hata! Response: {response.text[:200]}")
        
        # Hata detayını görmek için
        if response.status_code == 422:
            print("   Validation error - request formatı yanlış olabilir")
        elif response.status_code == 500:
            print("   Server error - API key veya başka bir sorun olabilir")
            
except Exception as e:
    print(f"   Upload hatası: {e}")
    
    # Hata detayını göster
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")

print("\n4. Alternatif test: JSON body ile yükleme...")
# Base64 encoded içerik
import base64
encoded_content = base64.b64encode(test_file_content).decode('utf-8')

json_data = {
    "files": [
        {
            "filename": "test_document.txt",
            "content": encoded_content
        }
    ]
}

try:
    headers_json = headers.copy()
    headers_json["Content-Type"] = "application/json"
    
    response = requests.post(
        f"{base_url}/add_documents/add",
        json=json_data,
        headers=headers_json,
        timeout=30
    )
    print(f"   JSON upload status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   JSON upload hatası: {e}")