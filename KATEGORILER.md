# Sağlık Mevzuatı Kategorileri

Bu belge, RAG sisteminde kullanılacak 8 ana kategoriyi tanımlar.

## 📋 Kategori Listesi

### 1. **Sağlık Personeli ve Meslek Düzenlemeleri**
- **Slug:** `saglik-personeli-ve-meslek`
- **Açıklama:** Hekim, hemşire, ebe, teknisyen düzenlemeleri, mesleki yeterlilik
- **Anahtar Kelimeler:** hekim, hemşire, ebe, teknisyen, meslek, yeterlilik, eğitim, sertifika
- **Örnek Mevzuat:** Hemşirelik Kanunu, Tababet Kanunu

### 2. **Sağlık Tesisleri ve Hizmet Sunumu**  
- **Slug:** `saglik-tesisleri-ve-hizmet`
- **Açıklama:** Hastane, klinik, sağlık ocağı işletmeciliği ve hizmet standartları
- **Anahtar Kelimeler:** hastane, klinik, tesis, hizmet, standart, akreditasyon, işletme
- **Örnek Mevzuat:** Sağlık Tesisleri Yönetmeliği

### 3. **İlaç ve Eczacılık Hizmetleri**
- **Slug:** `ilac-ve-eczacilik`
- **Açıklama:** İlaç temini, reçete sistemi, eczane işletmeciliği
- **Anahtar Kelimeler:** ilaç, eczane, reçete, farmasötik, doz, tedavi
- **Örnek Mevzuat:** Eczacılar ve Eczaneler Kanunu

### 4. **Ana Çocuk Sağlığı ve Aile Hekimliği**
- **Slug:** `ana-cocuk-ve-aile-hekimligi`  
- **Açıklama:** Bebek-çocuk izlem, ana sağlığı, aile hekimliği uygulamaları
- **Anahtar Kelimeler:** anne, bebek, çocuk, doğum, aile hekimi, izlem, neonatal
- **Örnek Mevzuat:** Aile Hekimliği Kanunu

### 5. **Halk Sağlığı ve Koruyucu Hizmetler**
- **Slug:** `halk-sagligi-ve-koruyucu`
- **Açıklama:** Kanser tarama, enfeksiyon kontrolü, aşılama, sürveyans
- **Anahtar Kelimeler:** halk sağlığı, tarama, aşı, enfeksiyon, koruyucu, önleyici
- **Örnek Mevzuat:** Kanser Tarama Programları

### 6. **Acil Sağlık ve Ambulans Hizmetleri**
- **Slug:** `acil-saglik-ve-ambulans`
- **Açıklama:** 112 acil çağrı, ambulans hizmetleri, acil müdahale
- **Anahtar Kelimeler:** acil, ambulans, 112, kurtarma, müdahale, teknisyen  
- **Örnek Mevzuat:** Ambulans ve Acil Bakım Teknikerleri Tebliği

### 7. **Yönetim ve Mali İşlemler**
- **Slug:** `yonetim-ve-mali-islemler`
- **Açıklama:** Bütçe, harcama belgeleri, idari süreçler
- **Anahtar Kelimeler:** yönetim, mali, bütçe, harcama, idari, süreç
- **Örnek Mevzuat:** Merkez Yönetim Harcama Belgeleri Yönetmeliği

### 8. **Zararlı Maddeler ve Sağlık Koruması**
- **Slug:** `zararli-maddeler-ve-koruma`
- **Açıklama:** Tütün kontrolü, alkol, zararlı madde düzenlemeleri
- **Anahtar Kelimeler:** tütün, sigara, nargile, alkol, zararlı, kontrol
- **Örnek Mevzuat:** Tütün Ürünlerinin Zararlarının Önlenmesi Kanunu

## 🔍 RAG Kullanımı

Bu kategoriler Qdrant metadata'sında `category` alanında saklanacak ve otomatik filtreleme için kullanılacaktır.

### Örnek Kullanım:
```python
# Kullanıcı: "nöbet kuralları"
# Sistem algılar: "saglik-personeli-ve-meslek" 
# Qdrant filter: category="saglik-personeli-ve-meslek"
```

## 📅 Son Güncelleme
Tarih: 2024-10-14
Versiyon: 1.0