import sys

print(f"Python sürümü: {sys.version}")
print(f"Python major version: {sys.version_info.major}")
print(f"Python minor version: {sys.version_info.minor}")

if sys.version_info >= (3, 10):
    print("✓ Python 3.10 veya üzeri - Google Generative AI ile uyumlu")
    
    # Google Generative AI'yı test et
    try:
        import google.generativeai as genai
        print("✓ google.generativeai modülü yüklendi")
        
        # API anahtarını test et
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            print(f"✓ GOOGLE_API_KEY mevcut: {api_key[:10]}...")
            
            try:
                genai.configure(api_key=api_key)
                print("✓ API anahtarı geçerli")
                
                # Basit test
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content("Merhaba")
                print(f"✓ Test başarılı: {response.text[:50]}...")
                
            except Exception as e:
                print(f"✗ API hatası: {e}")
        else:
            print("✗ GOOGLE_API_KEY bulunamadı")
            
    except ImportError as e:
        print(f"✗ google.generativeai modülü yüklenemedi: {e}")
        print("Lütfen şu komutu çalıştırın: pip install google-generativeai")
        
else:
    print("✗ Python 3.10'dan eski - Google Generative AI ile uyumsuz")
    print("Lütfen Python 3.10 veya üzerine yükseltin")