import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("=== PRODUCTION FRONTEND TESTİ ===")

# Production backend URL'i
production_url = "https://mevzusaglik.mevzusaglik.workers.dev"

# Database'deki API key
api_key = "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af"

print(f"Backend URL: {production_url}")
print(f"API Key: {api_key[:20]}...")

# 1. Önce login yapalım (kullanıcı oluşturalım)
print("\n1. Test kullanıcısı oluşturma/login...")

# Random kullanıcı adı oluştur
import random
import string
random_username = "testuser_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
password = "Test123!"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# Register
register_data = {
    "user_name": random_username,
    "password": password,
    "email": f"{random_username}@test.com"
}

try:
    response = requests.post(
        f"{production_url}/auth/register",
        json=register_data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"   ✓ Kullanıcı oluşturuldu: {random_username}")
        auth_data = response.json()
        session_uuid = auth_data.get("session_uuid")
        print(f"   Session UUID: {session_uuid}")
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"   ℹ️ Kullanıcı zaten var, login yapılıyor...")
        # Login yap
        login_data = {
            "user_name": random_username,
            "password": password
        }
        response = requests.post(
            f"{production_url}/auth/login",
            json=login_data,
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            auth_data = response.json()
            session_uuid = auth_data.get("session_uuid")
            print(f"   ✓ Login başarılı")
            print(f"   Session UUID: {session_uuid}")
        else:
            print(f"   ✗ Login hatası: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    else:
        print(f"   ✗ Register hatası: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ✗ Auth hatası: {e}")

# 2. Belge yükleme testi
print("\n2. Belge yükleme testi...")

# Test PDF içeriği
pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Production Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n0000000151 00000 n\n0000000222 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n281\n%%EOF"

try:
    files = {
        'files': ('production_test.pdf', pdf_content, 'application/pdf')
    }
    
    response = requests.post(
        f"{production_url}/add_documents/add",
        files=files,
        headers={"X-API-Key": api_key},  # Content-Type otomatik olarak multipart/form-data olacak
        timeout=30
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ BAŞARILI! Belge yüklendi!")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Message: {result.get('message')}")
        
        # Task status'unu kontrol et
        task_id = result.get('task_id')
        if task_id:
            print(f"\n3. Task status kontrolü (10 saniye bekleyelim)...")
            import time
            time.sleep(10)
            
            status_response = requests.get(
                f"{production_url}/add_documents/status/{task_id}",
                headers={"X-API-Key": api_key},
                timeout=10
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   Task Status: {status_data.get('status')}")
                print(f"   Message: {status_data.get('message')}")
            else:
                print(f"   Status kontrol hatası: {status_response.status_code}")
                print(f"   Response: {status_response.text[:200]}")
                
    elif response.status_code == 403:
        print(f"   ✗ API KEY HATASI! Geçersiz API anahtarı.")
        print(f"   Response: {response.text[:200]}")
        print("\n   ⚠️  Production frontend'i farklı bir API key kullanıyor olabilir!")
        print("   Hugging Face Spaces → Settings → Variables/Secrets kontrol edin.")
    else:
        print(f"   ✗ Hata! Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ✗ Upload hatası: {e}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()[:500]}")

print("\n=== TEST TAMAMLANDI ===")