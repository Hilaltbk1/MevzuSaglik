#!/usr/bin/env python3
"""
Aynı collection içindeki duplicate dosyaları temizler.
Aynı dosya adına sahip point'lerden sadece birini tutar, diğerlerini siler.
"""

import os
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env dosyası yüklendi")
except ImportError:
    print("⚠️  python-dotenv yüklü değil")

from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv("QDRANT_HOST", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
COLLECTION_NAME = "mevzuat_collection"

def main():
    print("=" * 70)
    print("QDRANT DUPLICATE FILES CLEANUP")
    print("=" * 70)
    
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ QDRANT_HOST veya QDRANT_API_KEY bulunamadı!")
        return
    
    print(f"\n📡 Qdrant'a bağlanılıyor: {QDRANT_HOST}")
    
    try:
        client = QdrantClient(
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            timeout=30,
        )
        print("✅ Bağlantı başarılı!")
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return
    
    if not client.collection_exists(COLLECTION_NAME):
        print(f"❌ Collection '{COLLECTION_NAME}' bulunamadı!")
        return
    
    print(f"\n📚 Collection '{COLLECTION_NAME}' taranıyor...")
    
    try:
        scroll_res, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=True,
        )
        print(f"✅ {len(scroll_res)} point bulundu")
    except Exception as e:
        print(f"❌ Tarama hatası: {e}")
        return
    
    # Dosya adlarına göre point'leri grupla
    file_groups = defaultdict(list)
    
    for point in scroll_res:
        if point.payload:
            filename = (
                point.payload.get("Mevzuat_Adi") or
                point.payload.get("Dosya_Adi") or
                point.payload.get("filename") or
                point.payload.get("file_name")
            )
            if filename:
                # Normalize et (lowercase, .pdf kaldır)
                normalized = filename.lower().replace('.pdf', '').strip()
                file_groups[normalized].append({
                    'id': point.id,
                    'original_name': filename,
                    'payload': point.payload
                })
    
    # Duplicate'leri bul
    duplicates = {name: points for name, points in file_groups.items() if len(points) > 1}
    
    print(f"\n📊 Analiz Sonuçları:")
    print(f"   📄 Toplam benzersiz dosya: {len(file_groups)}")
    print(f"   🔄 Duplicate dosya: {len(duplicates)}")
    
    if not duplicates:
        print("\n✅ Duplicate dosya bulunamadı! Collection temiz.")
        return
    
    # Duplicate'leri göster
    print(f"\n🔍 Duplicate Dosyalar:")
    total_to_delete = 0
    for idx, (name, points) in enumerate(sorted(duplicates.items()), 1):
        print(f"\n  {idx}. '{points[0]['original_name']}'")
        print(f"     🔄 {len(points)} kopya bulundu")
        print(f"     🗑️  {len(points) - 1} point silinecek")
        total_to_delete += len(points) - 1
    
    print(f"\n📊 Özet:")
    print(f"   🗑️  Toplam silinecek point: {total_to_delete}")
    print(f"   ✅ Korunacak point: {len(duplicates)}")
    
    # Onay iste
    print("\n" + "=" * 70)
    print(f"⚠️  UYARI: {total_to_delete} duplicate point SİLİNECEK!")
    print("=" * 70)
    
    response = input("\nDevam etmek istiyor musunuz? (evet/hayır): ").strip().lower()
    
    if response not in ['evet', 'yes', 'e', 'y']:
        print("\n❌ İşlem iptal edildi.")
        return
    
    # Duplicate'leri sil (her dosyadan ilkini tut, diğerlerini sil)
    print(f"\n🗑️  Duplicate'ler siliniyor...")
    deleted_count = 0
    
    for name, points in duplicates.items():
        # İlk point'i tut, diğerlerini sil
        points_to_delete = [p['id'] for p in points[1:]]
        
        try:
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=points_to_delete
            )
            deleted_count += len(points_to_delete)
            print(f"  ✅ '{points[0]['original_name']}': {len(points_to_delete)} kopya silindi")
        except Exception as e:
            print(f"  ❌ '{points[0]['original_name']}': Silme hatası - {e}")
    
    # Sonuç
    print("\n" + "=" * 70)
    print("✅ TEMİZLİK TAMAMLANDI!")
    print("=" * 70)
    print(f"🗑️  {deleted_count} duplicate point silindi")
    print(f"✅ {len(duplicates)} benzersiz dosya korundu")
    print(f"\n💡 Collection artık temiz! Her dosyadan sadece bir kopya var.")

if __name__ == "__main__":
    main()
