# Güvenlik ve Özellik Denetimi

## 🔍 KONTROL LİSTESİ

### 1. Plan Kalıcılığı
- [ ] Sayfa yenilendikten sonra plan değişmiyor mu?
- [ ] Pro plan seçiliyse Pro kalıyor mu?
- [ ] Ücretsiz plan seçiliyse Ücretsiz kalıyor mu?

### 2. Dosya Yükleme Kısıtlaması
- [ ] Ücretsiz plan: Dosya yükleme engelleniyor mu?
- [ ] Pro plan: Dosya yükleme çalışıyor mu?
- [ ] Unlimited plan: Dosya yükleme çalışıyor mu?

### 3. Oturum Yönetimi
- [ ] Çıkış yapınca oturum kapanıyor mu?
- [ ] Yeniden giriş yapınca yeni oturum oluşturuluyor mu?
- [ ] Eski oturum sohbet geçmişi sol taraftan erişilebiliyor mu?

### 4. Şifre Sıfırlama
- [ ] "Şifremi Unuttum" çalışıyor mu?
- [ ] Email'e kod gönderiliyor mu?
- [ ] Kod ile şifre sıfırlanıyor mu?

### 5. Güvenlik Açıkları
- [ ] API key'ler güvenli mi?
- [ ] SQL injection koruması var mı?
- [ ] CORS ayarları doğru mu?
- [ ] Tenant isolation sağlanıyor mu?

### 6. Veritabanı Sorunları
- [ ] User ID'ler neden 1'den başlamıyor?
- [ ] Tablo yapısı doğru mu?
- [ ] Foreign key'ler tanımlı mı?

## 📋 DETAYLI KONTROL

### Plan Kalıcılığı
**Dosya**: `frontend/index.html`
**Kontrol**: localStorage'da `ms_plan` kaydediliyor mu?

### Dosya Yükleme
**Dosya**: `backend/routers/add_documents.py`
**Kontrol**: Plan kontrolü yapılıyor mu?

### Oturum Yönetimi
**Dosya**: `backend/routers/session_router.py`
**Kontrol**: Session UUID'ler unique mi?

### Şifre Sıfırlama
**Dosya**: `backend/routers/auth_router.py`
**Kontrol**: Email gönderimi yapılıyor mu?

### Güvenlik
**Dosya**: `backend/dependencies/auth.py`
**Kontrol**: API key validation yapılıyor mu?

### Veritabanı
**Dosya**: `backend/schemas/user_model.py`
**Kontrol**: ID sequence doğru mu?
