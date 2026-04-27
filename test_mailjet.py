import os
from dotenv import load_dotenv
from mailjet_rest import Client

load_dotenv()

api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_API_SECRET")
from_email = os.getenv("MAILJET_FROM_EMAIL", "hilal.tabak826@gmail.com")
from_name = os.getenv("MAILJET_FROM_NAME", "MevzuSaglik")

print(f"🔍 Mailjet Debug - API Key: {api_key[:10]}...")
print(f"🔍 Mailjet Debug - From: {from_email}")

if not api_key or not api_secret:
    print("❌ API key eksik!")
    exit(1)

try:
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    token = "TEST123"
    to_email = "hilaltabak2021@gmail.com"
    
    body = f"""Merhaba,

Şifre sıfırlama talebiniz alındı.

Aşağıdaki kodu girin: {token}

Bu kod 30 dakika geçerlidir.

MevzuSaglik Ekibi"""

    data = {
        'Messages': [{
            'From': {'Email': from_email, 'Name': from_name},
            'To': [{'Email': to_email, 'Name': to_email}],
            'Subject': 'MevzuSaglik - Şifre Sıfırlama',
            'TextPart': body,
        }]
    }
    
    result = mailjet.send.create(data=data)
    print(f"Status: {result.status_code}")
    print(f"Response: {result.json()}")
    
    if result.status_code == 200:
        print("✅ E-posta başarıyla gönderildi!")
    else:
        print("❌ E-posta gönderilemedi")
        
except Exception as e:
    print(f"❌ Hata: {e}")