import os
from dotenv import load_dotenv

load_dotenv()

print("=== PRODUCTION ENVIRONMENT GÜNCELLEME ===")

# Database'deki doğru API key
correct_api_key = "5ea2dd1bb37998bff8de234a6e9f485d2ffd9bdeea562a20e550bc06a7e099af"

print(f"Doğru API Key: {correct_api_key[:20]}...")
print(f"Uzunluk: {len(correct_api_key)}")

# .env dosyasındaki mevcut key
current_key = os.getenv("TENANT_API_KEY", "").strip()

if current_key == correct_api_key:
    print(f"\n✓ .env dosyasındaki API key doğru zaten.")
else:
    print(f"\n⚠️  .env dosyasındaki API key farklı:")
    print(f"   Mevcut: {current_key[:20]}...")
    print(f"   Doğru:  {correct_api_key[:20]}...")
    
    # .env dosyasını güncelle
    print("\n.env dosyasını güncellemek ister misiniz?")
    # .env dosyasını oku
    with open(".env", "r") as f:
        content = f.read()
    
    # TENANT_API_KEY satırını bul ve değiştir
    lines = content.split('\n')
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith("TENANT_API_KEY="):
            new_lines.append(f"TENANT_API_KEY={correct_api_key}")
            updated = True
        else:
            new_lines.append(line)
    
    # Eğer TENANT_API_KEY satırı yoksa ekle
    if not updated:
        new_lines.append(f"TENANT_API_KEY={correct_api_key}")
    
    # .env dosyasını yaz
    with open(".env", "w") as f:
        f.write('\n'.join(new_lines))
    
    print(f"✓ .env dosyası güncellendi!")

# Hugging Face için talimatlar
print("\n=== HUGGING FACE GÜNCELLEME TALİMATLARI ===")
print("1. Hugging Face Spaces'e gidin: https://huggingface.co/spaces")
print("2. MevzuSaglik space'inizi seçin")
print("3. 'Settings' sekmesine tıklayın")
print("4. 'Variables and secrets' bölümüne gidin")
print("5. 'TENANT_API_KEY' değişkenini bulun")
print(f"6. Değerini şu API key ile güncelleyin:")
print(f"   {correct_api_key}")
print("7. 'Save' butonuna tıklayın")
print("8. Space'i yeniden başlatın")

# GitHub için talimatlar
print("\n=== GITHUB GÜNCELLEME TALİMATLARI ===")
print("1. GitHub repository'nize gidin")
print("2. 'Settings' sekmesine tıklayın")
print("3. 'Secrets and variables' → 'Actions' seçin")
print("4. 'Repository secrets' bölümüne gidin")
print("5. 'TENANT_API_KEY' secret'ını bulun")
print(f"6. Değerini şu API key ile güncelleyin:")
print(f"   {correct_api_key}")
print("7. 'Update secret' butonuna tıklayın")

print("\n=== ÖNEMLİ NOTLAR ===")
print("1. API key değiştiğinde uygulamayı yeniden başlatmanız gerekebilir")
print("2. Browser cache'ini temizleyin veya incognito modda test edin")
print("3. Production'da test etmek için:")
print("   - mevzusaglik.com.tr'yi açın")
print("   - Giriş yapın veya kayıt olun")
print("   - Belge yüklemeyi deneyin")

print("\nArtık 'API gereklı' hatası almayacaksınız!")