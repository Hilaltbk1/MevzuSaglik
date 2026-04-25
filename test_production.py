import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Production backend URL'i
production_url = "https://mevzusaglik.mevzusaglik.workers.dev"
# Localhost'ta çalışan API key (database'de var)
api_key = "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af"

print(f"Production URL: {production_url}")
print(f"API Key: {api_key[:20]}...")

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# 1. Health endpoint'ini test et
print("\n1. Health endpoint testi...")
try:
    response = requests.get(f"{production_url}/health", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   Hata: {e}")

# 2. Belge yükleme endpoint'ini test et
print("\n2. Belge yükleme endpoint testi...")
try:
    # Basit bir test
    response = requests.get(f"{production_url}/add_documents/status/test", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   Hata: {e}")

# 3. CORS kontrolü (OPTIONS request)
print("\n3. CORS kontrolü...")
try:
    response = requests.options(f"{production_url}/add_documents/add", timeout=10)
    print(f"   OPTIONS Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
except Exception as e:
    print(f"   Hata: {e}")