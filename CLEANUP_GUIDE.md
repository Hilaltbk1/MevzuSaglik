# 🧹 Qdrant Duplicate Temizleme Rehberi

Bu rehber, Qdrant Cloud'daki duplicate dosyaları temizlemek için hazırlanmıştır.

## 📋 İki Tür Duplicate Var

### 1. **Duplicate Collection'lar**
- `mevzuat_collection` (Ana - Kullanılıyor ✅)
- `mevzu_saglik_docs` (Eski - Silinmeli ❌)

### 2. **Aynı Collection İçinde Duplicate Dosyalar**
- Aynı dosya birden fazla kez yüklenmiş
- Örnek: `dosya.pdf` 3 kez yüklenmiş → 3 kopya var

---

## 🗑️ Yöntem 1: Duplicate Collection'ı Sil

### Script ile (Önerilen)

```bash
# 1. Script'i çalıştır
python cleanup_duplicates.py

# 2. Çıktıyı incele
📚 Mevcut collection'lar:
  1. mevzuat_collection
  2. mevzu_saglik_docs

✅ Ana collection mevcut:
   📦 1250 point
   📄 15 benzersiz dosya

⚠️  Eski collection bulundu:
   📦 800 point
   📄 10 benzersiz dosya

# 3. Onay ver
Devam etmek istiyor musunuz? (evet/hayır): evet

# 4. Sonuç
✅ TEMİZLİK TAMAMLANDI!
✅ Ana collection 'mevzuat_collection' korundu
🗑️  Eski collection 'mevzu_saglik_docs' silindi
```

### Manuel (Qdrant Dashboard)

1. https://cloud.qdrant.io/ adresine git
2. Cluster'ınızı seç
3. **Collections** sekmesine git
4. `mevzu_saglik_docs` collection'ını bul
5. **Delete** butonuna tıkla
6. Onay ver

---

## 🗑️ Yöntem 2: Aynı Collection İçindeki Duplicate'leri Sil

### Script ile

```bash
# 1. Script'i çalıştır
python remove_duplicate_files.py

# 2. Çıktıyı incele
📊 Analiz Sonuçları:
   📄 Toplam benzersiz dosya: 15
   🔄 Duplicate dosya: 3

🔍 Duplicate Dosyalar:

  1. 'Hemşirelik Yönetmeliği.pdf'
     🔄 3 kopya bulundu
     🗑️  2 point silinecek

  2. 'Sağlık Bakanlığı Tebliği.pdf'
     🔄 2 kopya bulundu
     🗑️  1 point silinecek

📊 Özet:
   🗑️  Toplam silinecek point: 3
   ✅ Korunacak point: 3

# 3. Onay ver
Devam etmek istiyor musunuz? (evet/hayır): evet

# 4. Sonuç
✅ TEMİZLİK TAMAMLANDI!
🗑️  3 duplicate point silindi
✅ 3 benzersiz dosya korundu
```

---

## 🎯 Hangi Script'i Kullanmalıyım?

### `cleanup_duplicates.py` - Collection Temizliği
**Ne zaman kullan:**
- İki farklı collection varsa
- `mevzu_saglik_docs` collection'ını silmek istiyorsan
- Tüm collection'ı temizlemek istiyorsan

**Sonuç:**
- ✅ `mevzuat_collection` korunur
- 🗑️ `mevzu_saglik_docs` silinir

### `remove_duplicate_files.py` - Dosya Temizliği
**Ne zaman kullan:**
- Aynı dosyayı birden fazla kez yüklediysen
- Tek collection içinde duplicate'ler varsa
- Sadece duplicate dosyaları temizlemek istiyorsan

**Sonuç:**
- ✅ Her dosyadan 1 kopya kalır
- 🗑️ Diğer kopyalar silinir

---

## 🚀 Önerilen Sıra

1. **Önce:** `cleanup_duplicates.py` çalıştır
   - Eski collection'ı temizle

2. **Sonra:** `remove_duplicate_files.py` çalıştır
   - Ana collection içindeki duplicate'leri temizle

3. **Test et:**
   - Var olan bir dosyayı tekrar yüklemeyi dene
   - "🚫 Dosya zaten mevcut" mesajı almalısın

---

## ⚠️ Önemli Notlar

1. **Yedek almayı unutma!**
   - Script'ler kalıcı olarak siler
   - Geri alma yok

2. **Önce test et:**
   - Script'i çalıştır
   - Çıktıyı incele
   - Sonra onay ver

3. **Environment variable'lar:**
   - `.env` dosyasında olmalı:
     ```
     QDRANT_HOST=https://...
     QDRANT_API_KEY=...
     ```

4. **Hugging Face'de çalıştır:**
   - Lokal'de değil, Hugging Face'de çalıştır
   - Çünkü environment variable'lar orada

---

## 🧪 Test Komutları

### Collection'ları Listele
```bash
python test_duplicate_check.py
```

### Duplicate'leri Kontrol Et (Silmeden)
```bash
# Script'i çalıştır ama "hayır" de
python remove_duplicate_files.py
# Çıktıyı incele, "hayır" de
```

---

## 📞 Sorun mu Var?

Script hata verirse:
1. `.env` dosyasını kontrol et
2. Qdrant bağlantısını test et
3. Collection adını kontrol et
4. Logları oku

---

## ✅ Başarı Kriterleri

Temizlik başarılı olduysa:
- ✅ Sadece `mevzuat_collection` var
- ✅ Her dosyadan 1 kopya var
- ✅ Duplicate yükleme engelleniyor
- ✅ Loglar doğru collection'ı gösteriyor

---

**Son Güncelleme:** 2026-04-25
