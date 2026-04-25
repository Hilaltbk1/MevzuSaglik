import requests
import os

# Test doğrudan Hugging Face'e
API_KEY = "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af"
BACKEND_URL = "https://hilal1-mevzusaglik.hf.space"

headers = {"X-API-Key": API_KEY}

print("1. GET /test testi:")
try:
    response = requests.get(f"{BACKEND_URL}/test", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. POST /add_documents/add testi (no file):")
try:
    response = requests.post(f"{BACKEND_URL}/add_documents/add", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. Cloudflare Worker testi:")
try:
    response = requests.post("https://mevzusaglik.com.tr/add_documents/add", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")