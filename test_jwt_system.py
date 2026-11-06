#!/usr/bin/env python3
"""
JWT Authentication System Test Script
Bu script yeni JWT sisteminin çalışıp çalışmadığını test eder
"""

import requests
import json
import sys
from datetime import datetime

# Test Ayarları
BASE_URL = "http://localhost:8000"  # Backend URL'si
TEST_USER = {
    "user_name": f"test_user_{datetime.now().strftime('%H%M%S')}",
    "password": "TestPass123!",
    "email": f"test_{datetime.now().strftime('%H%M%S')}@test.com"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_header(title):
    print(f"\n{Colors.BOLD}🔧 {title}{Colors.END}")
    print("=" * (len(title) + 4))

def test_api_call(method, endpoint, data=None, headers=None, expected_status=200):
    """API çağrısı yapar ve sonucu test eder"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Desteklenmeyen HTTP method: {method}")
        
        print_info(f"{method} {endpoint} → Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print_success(f"Beklenen status code alındı: {expected_status}")
            try:
                return True, response.json()
            except:
                return True, response.text
        else:
            print_error(f"Beklenen: {expected_status}, Alınan: {response.status_code}")
            try:
                error_detail = response.json()
                print_error(f"Hata detayı: {error_detail}")
            except:
                print_error(f"Hata detayı: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print_error(f"Backend'e bağlanılamıyor! {BASE_URL} çalışıyor mu?")
        return False, None
    except Exception as e:
        print_error(f"Beklenmeyen hata: {str(e)}")
        return False, None

def main():
    print_header("JWT AUTHENTICATION SİSTEMİ TEST")
    
    access_token = None
    all_tests_passed = True
    
    # Test 1: Backend çalışıyor mu?
    print_header("Test 1: Backend Bağlantısı")
    success, response = test_api_call("GET", "/")
    if not success:
        print_error("Backend çalışmıyor! Test durduruluyor.")
        sys.exit(1)
    print_success("Backend çalışıyor!")
    
    # Test 2: Kullanıcı Kaydı
    print_header("Test 2: Kullanıcı Kaydı (Register)")
    success, response = test_api_call("POST", "/auth/register", TEST_USER, expected_status=200)
    
    if success and response:
        if "access_token" in response:
            access_token = response["access_token"]
            print_success(f"Kayıt başarılı! Token alındı: {access_token[:20]}...")
            print_info(f"Kullanıcı: {response.get('user_name')}")
            print_info(f"Tenant ID: {response.get('tenant_id')}")
        else:
            print_error("Kayıt yapıldı ama access_token dönmedi!")
            all_tests_passed = False
    else:
        print_error("Kullanıcı kaydı başarısız!")
        all_tests_passed = False
        
    # Test 3: Token ile /auth/me
    print_header("Test 3: Token Doğrulama (/auth/me)")
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        success, response = test_api_call("GET", "/auth/me", headers=headers)
        
        if success and response:
            print_success("Token geçerli! Kullanıcı bilgileri alındı:")
            print_info(f"  User ID: {response.get('user_id')}")
            print_info(f"  Username: {response.get('username')}")
            print_info(f"  Email: {response.get('email')}")
            print_info(f"  Role: {response.get('role')}")
            print_info(f"  Tenant ID: {response.get('tenant_id')}")
        else:
            print_error("Token ile kullanıcı bilgileri alınamadı!")
            all_tests_passed = False
    else:
        print_warning("Token olmadığı için bu test atlanıyor")
        all_tests_passed = False
    
    # Test 4: Korumalı endpoint (/search/ask)
    print_header("Test 4: Korumalı API Endpoint (/search/ask)")
    if access_token:
        search_data = {
            "message": "Test sorusu: Sağlık hakkında bilgi",
            "session_uuid": "test-session-uuid",
            "user_name": TEST_USER["user_name"]
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        success, response = test_api_call("POST", "/search/ask", search_data, headers=headers)
        
        if success:
            print_success("Korumalı endpoint erişimi başarılı!")
        else:
            print_error("Korumalı endpoint erişimi başarısız!")
            all_tests_passed = False
    else:
        print_warning("Token olmadığı için bu test atlanıyor")
        all_tests_passed = False
    
    # Test 5: Logout
    print_header("Test 5: Güvenli Çıkış (Logout)")
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        success, response = test_api_call("POST", "/auth/logout", headers=headers)
        
        if success:
            print_success("Logout başarılı!")
        else:
            print_error("Logout başarısız!")
            all_tests_passed = False
    else:
        print_warning("Token olmadığı için bu test atlanıyor")
        all_tests_passed = False
    
    # Test 6: Logout sonrası token geçersiz mi?
    print_header("Test 6: Logout Sonrası Token Kontrolü")
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        success, response = test_api_call("GET", "/auth/me", headers=headers, expected_status=401)
        
        if success:
            print_success("Token başarıyla iptal edildi! (401 alındı)")
        else:
            print_error("Token hala geçerli! Logout çalışmadı!")
            all_tests_passed = False
    else:
        print_warning("Token olmadığı için bu test atlanıyor")
        all_tests_passed = False
    
    # Test 7: Yeniden Login
    print_header("Test 7: Yeniden Giriş (Login)")
    login_data = {
        "user_name": TEST_USER["user_name"],
        "password": TEST_USER["password"]
    }
    success, response = test_api_call("POST", "/auth/login", login_data)
    
    if success and response and "access_token" in response:
        new_token = response["access_token"]
        print_success(f"Yeniden giriş başarılı! Yeni token: {new_token[:20]}...")
        
        # Yeni token ile /auth/me test et
        headers = {"Authorization": f"Bearer {new_token}"}
        success, response = test_api_call("GET", "/auth/me", headers=headers)
        if success:
            print_success("Yeni token ile kullanıcı bilgileri alındı!")
        else:
            print_error("Yeni token çalışmıyor!")
            all_tests_passed = False
    else:
        print_error("Yeniden giriş başarısız!")
        all_tests_passed = False
    
    # Test 8: Geçersiz token testi
    print_header("Test 8: Geçersiz Token Testi")
    fake_headers = {"Authorization": "Bearer fake_token_123"}
    success, response = test_api_call("GET", "/auth/me", headers=fake_headers, expected_status=401)
    if success:
        print_success("Geçersiz token reddedildi! (401 alındı)")
    else:
        print_error("Geçersiz token kabul edildi! Güvenlik riski!")
        all_tests_passed = False
    
    # SONUÇ
    print_header("TEST SONUÇLARI")
    if all_tests_passed:
        print_success("🎉 TÜM TESTLER BAŞARILI!")
        print_success("JWT Authentication sistemi tam olarak çalışıyor!")
        print_info("\n✅ Yapabileceklerin:")
        print_info("  • Kullanıcı kaydı ve girişi")
        print_info("  • Token tabanlı API erişimi")  
        print_info("  • Güvenli çıkış")
        print_info("  • Token doğrulama")
        print_info("  • Korumalı endpoint'ler")
        print_info("\n🚀 Sonraki adım: Frontend'i JWT sistemine adapte et")
    else:
        print_error("❌ BAZI TESTLER BAŞARISIZ!")
        print_warning("Hatalar olabilir, logları kontrol et")
        print_info("\n🔧 Yapılacaklar:")
        print_info("  • Backend loglarını kontrol et")
        print_info("  • Veritabanı bağlantısını kontrol et")
        print_info("  • JWT ayarlarını kontrol et")
    
    return all_tests_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTest kullanıcı tarafından durduruldu")
        sys.exit(1)
    except Exception as e:
        print_error(f"Beklenmeyen hata: {str(e)}")
        sys.exit(1)