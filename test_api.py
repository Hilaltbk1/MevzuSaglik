import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API key from environment
API_KEY = os.getenv("TENANT_API_KEY")
BACKEND_URL = "https://hilal1-mevzusaglik.hf.space"

def test_api_key():
    """Test API key validation"""
    print(f"Testing API key: {API_KEY[:10]}...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    # Test 1: Simple GET request
    try:
        response = requests.get(f"{BACKEND_URL}/test", headers=headers)
        print(f"GET /test: {response.status_code} - {response.text[:50]}")
    except Exception as e:
        print(f"GET /test error: {e}")
    
    # Test 2: POST to add_documents (without file)
    try:
        response = requests.post(f"{BACKEND_URL}/add_documents/add", headers=headers)
        print(f"POST /add_documents/add (no file): {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"POST /add_documents/add error: {e}")
    
    # Test 3: Test with domain
    domain_url = "https://mevzusaglik.com.tr"
    try:
        response = requests.post(f"{domain_url}/add_documents/add", headers=headers)
        print(f"POST domain /add_documents/add: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"Domain POST error: {e}")

if __name__ == "__main__":
    test_api_key()