#!/usr/bin/env python3
"""API key'in doğru olup olmadığını test et"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "https://mevzusaglik.com.tr"

# Test API keys
api_keys = {
    "free": "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af",
    "pro": "60f1d84f0c61a664b3eb9ad57afcba7f0d3dd2780a4418395171d7250432395d",
    "unlimited": "01fdd7b2dc26de0c5c9db75081a6ca04699444d72595d2829098882e546cb921"
}

print("=" * 80)
print("API KEY TEST")
print("=" * 80)

for plan, api_key in api_keys.items():
    print(f"\n{plan.upper()} Plan:")
    print(f"  API Key: {api_key}")
    
    # Test /session/create_session
    try:
        res = requests.post(
            f"{BACKEND_URL}/session/create_session",
            json={"user_name": "test"},
            headers={"X-API-Key": api_key},
            timeout=10
        )
        print(f"  /session/create_session: {res.status_code}")
        if res.status_code != 200:
            print(f"    Error: {res.text[:100]}")
    except Exception as e:
        print(f"  /session/create_session: ERROR - {str(e)[:50]}")

print("\n" + "=" * 80)
