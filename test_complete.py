import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TENANT_API_KEY")
HEADERS = {"X-API-Key": API_KEY}

def test_all_endpoints():
    print("=== COMPLETE API TEST ===\n")
    
    # Test endpoints
    endpoints = [
        ("GET", "https://hilal1-mevzusaglik.hf.space/test", "Backend test"),
        ("GET", "https://mevzusaglik.com.tr/test", "Domain test"),
        ("POST", "https://hilal1-mevzusaglik.hf.space/add_documents/add", "Hugging Face upload (no file)"),
        ("POST", "https://mevzusaglik.com.tr/add_documents/add", "Domain upload (no file)"),
        ("POST", "https://hilal1-mevzusaglik.hf.space/chat", "Chat endpoint"),
    ]
    
    for method, url, description in endpoints:
        print(f"\nTesting: {description}")
        print(f"URL: {url}")
        print(f"Method: {method}")
        print(f"API Key: {API_KEY[:10]}...")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=HEADERS)
            else:  # POST
                # For chat endpoint, send minimal data
                if "chat" in url:
                    data = {"message": "test", "user_name": "test", "session_uuid": "test", "user_id": "test"}
                    response = requests.post(url, json=data, headers=HEADERS)
                else:
                    # For upload endpoints, send empty request
                    response = requests.post(url, headers=HEADERS)
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            if response.status_code == 405:
                print("⚠️ 405 Method Not Allowed - Cloudflare Worker needs fixing")
            elif response.status_code == 422:
                print("✅ 422 Unprocessable Entity - Expected (no file provided)")
            elif response.status_code == 200:
                print("✅ Success!")
            elif response.status_code == 403:
                print("❌ 403 Forbidden - API key validation failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_all_endpoints()