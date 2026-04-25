import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API anahtarı
api_key = os.getenv("TENANT_API_KEY", "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af")
base_url = "http://127.0.0.1:8000"

headers = {
    "X-API-Key": api_key,
}

print(f"API Key: {api_key[:10]}...")
print(f"Base URL: {base_url}")

# Test PDF dosyasını oku
with open("test.pdf", "rb") as f:
    pdf_content = f.read()

print(f"PDF dosya boyutu: {len(pdf_content)} bytes")

# Multipart form data ile yükleme
files = {
    'files': ('test_saglik_mevzuati.pdf', pdf_content, 'application/pdf')
}

print("\nPDF dosyası yükleniyor...")
try:
    response = requests.post(
        f"{base_url}/add_documents/add",
        files=files,
        headers=headers,
        timeout=60  # Daha uzun timeout, işlem zaman alabilir
    )
    print(f"Upload status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Başarılı!")
        print(f"  Task ID: {result.get('task_id')}")
        print(f"  Mesaj: {result.get('message')}")
        
        # Task status'unu kontrol et
        task_id = result.get('task_id')
        if task_id:
            print(f"\nTask status kontrol ediliyor (5 saniye bekleyelim)...")
            import time
            time.sleep(5)
            
            status_response = requests.get(
                f"{base_url}/add_documents/status/{task_id}",
                headers=headers,
                timeout=10
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  Task Status: {status_data.get('status')}")
                print(f"  Mesaj: {status_data.get('message')}")
            else:
                print(f"  Status kontrol hatası: {status_response.status_code}")
                
    else:
        print(f"✗ Hata! Status: {response.status_code}")
        print(f"  Response: {response.text[:500]}")
        
except Exception as e:
    print(f"✗ Upload hatası: {e}")
    
    # Daha detaylı hata bilgisi
    import traceback
    print(f"  Traceback: {traceback.format_exc()[:500]}")

print("\n--- Test Tamamlandı ---")