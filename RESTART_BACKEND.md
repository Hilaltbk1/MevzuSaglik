# Backend'i Yeniden Başlatma Talimatları

## Sorun:
- Kod değişiklikleri yapıldı (collection adı `mevzu_saglik_docs` olarak güncellendi)
- Backend hala eski kodu çalıştırıyor
- 500 hatası alınıyor

## Çözüm:

### Hugging Face Spaces'te Restart:

1. **Hugging Face'e git**: https://huggingface.co/spaces/hilal1/mevzusaglik

2. **Settings sekmesine tıkla**

3. **"Factory reboot" butonuna bas** (veya "Restart this Space")

4. **Bekle**: Space yeniden başlatılacak (1-2 dakika sürebilir)

### Alternatif: Git Push ile Restart

Eğer yukarıdaki yöntem çalışmazsa, boş bir commit yaparak Space'i restart edebilirsiniz:

```bash
# Boş commit yap
git commit --allow-empty -m "Restart backend"

# Push et
git push
```

### Kontrol:

Backend başladıktan sonra test edin:

```bash
curl https://hilal1-mevzusaglik.hf.space/test
```

Başarılı yanıt:
```json
{
  "status": "ok",
  "message": "Backend çalışıyor"
}
```

### Log Kontrolü:

Hugging Face Spaces'te "Logs" sekmesinden backend loglarını kontrol edin:

✅ Görmek istediğiniz:
```
✅ Mevcut collection 'mevzu_saglik_docs' kullanılıyor.
```

❌ Görmek istemediğiniz:
```
❌ Collection 'mevzuat_collection' bulunamadı!
```

## Özet:

1. Hugging Face Spaces → Settings → Factory Reboot
2. 1-2 dakika bekle
3. Frontend'i yenile ve test et
