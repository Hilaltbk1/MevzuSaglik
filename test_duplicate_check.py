#!/usr/bin/env python3
"""
Duplicate dosya kontrolünü test etmek için script.
Qdrant'taki mevcut dosyaları listeler.
"""

import os
import sys

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env dosyası yüklendi")
except ImportError:
    print("⚠️  python-dotenv yüklü değil, environment variable'lar manuel yüklenecek")

from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv("QDRANT_HOST", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
COLLECTION_NAME = "mevzu_saglik_docs"  # Qdrant'taki gerçek collection adı

def main():
    print("=" * 60)
    print("QDRANT DUPLICATE CHECK TEST")
    print("=" * 60)
    
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ QDRANT_HOST veya QDRANT_API_KEY bulunamadı!")
        print("   .env dosyasını kontrol edin veya environment variable'ları ayarlayın.")
        print("\n💡 Kullanım:")
        print("   QDRANT_HOST=https://... QDRANT_API_KEY=... python test_duplicate_check.py")
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
        print(f"\n⚠️  Collection '{COLLECTION_NAME}' bulunamadı!")
        return
    
    print(f"\n📚 Collection '{COLLECTION_NAME}' kontrol ediliyor...")
    
    try:
        scroll_res, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=True,
        )
        
        print(f"✅ Toplam {len(scroll_res)} point bulundu\n")
        
        # Dosya adlarını topla
        files = {}
        for point in scroll_res:
            if point.payload:
                filename = None
                
                # Önce root level'da ara
                filename = (
                    point.payload.get("Mevzuat_Adi") or
                    point.payload.get("Dosya_Adi") or
                    point.payload.get("filename") or
                    point.payload.get("file_name")
                )
                
                # Bulamazsa metadata object'inin içinde ara
                if not filename and "metadata" in point.payload:
                    metadata_obj = point.payload["metadata"]
                    if isinstance(metadata_obj, dict):
                        filename = (
                            metadata_obj.get("Mevzuat_Adi") or
                            metadata_obj.get("Dosya_Adi") or
                            metadata_obj.get("filename") or
                            metadata_obj.get("file_name") or
                            metadata_obj.get("Mevzuat Adı") or
                            metadata_obj.get("Dosya Adı")
                        )
                
                if filename:
                    if filename not in files:
                        files[filename] = 0
                    files[filename] += 1
        
        print("=" * 60)
        print("QDRANT'TAKİ DOSYALAR (RAG için işlenmiş)")
        print("=" * 60)
        
        if not files:
            print("⚠️  Hiç dosya bulunamadı!")
        else:
            for idx, (filename, count) in enumerate(sorted(files.items()), 1):
                print(f"{idx:3d}. {filename:50s} ({count} chunk)")
        
        print("\n" + "=" * 60)
        print(f"TOPLAM: {len(files)} benzersiz dosya, {len(scroll_res)} chunk")
        print("=" * 60)
        
        print("\n💡 Bu dosyalardan birini tekrar yüklemeyi denerseniz,")
        print("   sistem '⚠️ Dosya zaten Qdrant'ta mevcut' uyarısı verecek.")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
