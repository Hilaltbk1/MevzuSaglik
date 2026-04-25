#!/usr/bin/env python3
"""
Qdrant'taki duplicate collection'ları temizler.
UYARI: Bu script collection'ları kalıcı olarak siler!
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env dosyası yüklendi")
except ImportError:
    print("⚠️  python-dotenv yüklü değil")

from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv("QDRANT_HOST", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()

# Collection adları
MAIN_COLLECTION = "mevzu_saglik_docs"  # Ana collection (korunacak)
OLD_COLLECTION = "mevzuat_collection"   # Eski collection (varsa silinecek)

def main():
    print("=" * 70)
    print("QDRANT DUPLICATE COLLECTION CLEANUP")
    print("=" * 70)
    
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ QDRANT_HOST veya QDRANT_API_KEY bulunamadı!")
        print("   .env dosyasını kontrol edin.")
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
    
    # Tüm collection'ları listele
    print("\n📚 Mevcut collection'lar:")
    try:
        collections = client.get_collections().collections
        for idx, col in enumerate(collections, 1):
            print(f"  {idx}. {col.name}")
    except Exception as e:
        print(f"❌ Collection'lar listelenemedi: {e}")
        return
    
    # Ana collection'ı kontrol et
    print(f"\n🔍 Ana collection kontrol ediliyor: '{MAIN_COLLECTION}'")
    if not client.collection_exists(MAIN_COLLECTION):
        print(f"⚠️  Ana collection '{MAIN_COLLECTION}' bulunamadı!")
        print("   Bu collection'ı silmeden önce oluşturmanız gerekebilir.")
    else:
        # Ana collection'daki dosya sayısını göster
        try:
            scroll_res, _ = client.scroll(
                collection_name=MAIN_COLLECTION,
                limit=10000,
                with_payload=True,
            )
            
            # Benzersiz dosyaları say
            unique_files = set()
            for point in scroll_res:
                if point.payload:
                    filename = (
                        point.payload.get("Mevzuat_Adi") or
                        point.payload.get("Dosya_Adi") or
                        point.payload.get("filename") or
                        point.payload.get("file_name")
                    )
                    if filename:
                        unique_files.add(filename)
            
            print(f"✅ Ana collection mevcut:")
            print(f"   📦 {len(scroll_res)} point")
            print(f"   📄 {len(unique_files)} benzersiz dosya")
            
            if unique_files:
                print(f"   📋 İlk 5 dosya: {', '.join(sorted(list(unique_files)[:5]))}")
        except Exception as e:
            print(f"⚠️  Ana collection bilgileri alınamadı: {e}")
    
    # Eski collection'ı kontrol et
    print(f"\n🔍 Eski collection kontrol ediliyor: '{OLD_COLLECTION}'")
    if not client.collection_exists(OLD_COLLECTION):
        print(f"✅ Eski collection '{OLD_COLLECTION}' zaten yok. Temizlik gerekmiyor!")
        return
    
    # Eski collection'daki dosya sayısını göster
    try:
        scroll_res, _ = client.scroll(
            collection_name=OLD_COLLECTION,
            limit=10000,
            with_payload=True,
        )
        
        # Benzersiz dosyaları say
        unique_files = set()
        for point in scroll_res:
            if point.payload:
                filename = (
                    point.payload.get("Mevzuat_Adi") or
                    point.payload.get("Dosya_Adi") or
                    point.payload.get("filename") or
                    point.payload.get("file_name")
                )
                if filename:
                    unique_files.add(filename)
        
        print(f"⚠️  Eski collection bulundu:")
        print(f"   📦 {len(scroll_res)} point")
        print(f"   📄 {len(unique_files)} benzersiz dosya")
        
        if unique_files:
            print(f"   📋 İlk 5 dosya: {', '.join(sorted(list(unique_files)[:5]))}")
    except Exception as e:
        print(f"⚠️  Eski collection bilgileri alınamadı: {e}")
    
    # Onay iste
    print("\n" + "=" * 70)
    print(f"⚠️  UYARI: '{OLD_COLLECTION}' collection'ı SİLİNECEK!")
    print(f"✅ '{MAIN_COLLECTION}' collection'ı KORUNACAK.")
    print("=" * 70)
    
    response = input("\nDevam etmek istiyor musunuz? (evet/hayır): ").strip().lower()
    
    if response not in ['evet', 'yes', 'e', 'y']:
        print("\n❌ İşlem iptal edildi.")
        return
    
    # Eski collection'ı sil
    print(f"\n🗑️  '{OLD_COLLECTION}' collection'ı siliniyor...")
    try:
        client.delete_collection(OLD_COLLECTION)
        print(f"✅ '{OLD_COLLECTION}' başarıyla silindi!")
    except Exception as e:
        print(f"❌ Silme hatası: {e}")
        return
    
    # Sonuç
    print("\n" + "=" * 70)
    print("✅ TEMİZLİK TAMAMLANDI!")
    print("=" * 70)
    print(f"✅ Ana collection '{MAIN_COLLECTION}' korundu")
    print(f"🗑️  Eski collection '{OLD_COLLECTION}' silindi")
    print("\n💡 Artık tüm dosya yüklemeleri '{MAIN_COLLECTION}' collection'ına yapılacak.")
    print("💡 Duplicate kontrolü doğru çalışacak.")

if __name__ == "__main__":
    main()
