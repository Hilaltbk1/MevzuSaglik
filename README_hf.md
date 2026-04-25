# MevzuSağlık AI - Hugging Face Spaces

Bu depo, Hugging Face Spaces üzerinde çalışan MevzuSağlık AI asistanının demo sürümüdür.

## Özellikler

- FastAPI backend
- Basit chat arayüzü
- Hugging Face Spaces uyumlu
- Python 3.10+ desteği

## Kurulum (Hugging Face Spaces için)

1. **Hugging Face Spaces'te yeni space oluşturun**
   - App type: **Gradio** veya **Static**
   - Hardware: **CPU Basic** (ücretsiz)

2. **Bu dosyaları yükleyin:**
   - `app.py` (ana uygulama)
   - `requirements_hf.txt` (bağımlılıklar)
   - `README.md` (açıklama)

3. **Space ayarları:**
   - Python version: **3.10**
   - Secrets: Gerekli API key'leri (GOOGLE_API_KEY, vs.)

## Yerel Çalıştırma

```bash
# Bağımlılıkları yükle
pip install -r requirements_hf.txt

# Uygulamayı başlat
python app.py
```

Uygulama `http://localhost:7860` adresinde çalışacaktır.

## Endpoint'ler

- `GET /` - Ana sayfa
- `GET /health` - Sağlık kontrolü
- `POST /chat` - Chat endpoint'i
- `GET /ui` - Web arayüzü

## Hugging Face Spaces Linki

Uygulamanız şu adreste çalışacak:
`https://huggingface.co/spaces/{kullanici_adi}/mevzusaglik`

## Sorun Giderme

1. **"Your space is in error" hatası:**
   - Python sürümünü 3.10 yapın
   - `requirements_hf.txt` kullanın
   - Logları kontrol edin

2. **Import hataları:**
   - `langchain` ve `langchain-community` sürümlerini kontrol edin
   - Python 3.10 kullanın

3. **CORS hataları:**
   - CORS ayarlarını `app.py` dosyasında güncelleyin