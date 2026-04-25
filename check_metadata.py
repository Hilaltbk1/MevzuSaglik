#!/usr/bin/env python3
"""
Qdrant'taki point'lerin metadata'sını kontrol eder.
Dosya adı field'larını gösterir.
"""

import os
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env dosyası yüklendi")
except ImportError:
    print("⚠️  python-dotenv yüklü değil")

from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv("QDRANT_HOST", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
COLLECTION_NAME = "mevzu_saglik_docs"

def main():
    print("=" * 70)
    print("QDRANT METADATA CHECKER")
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
        # İlk 100 point'i al
        scroll_res, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            with_payload=True,
        )
        print(f"✅ {len(scroll_res)} point alındı (örnek)\n")
        
        # Metadata field'larını topla
        all_fields = Counter()
        sample_payloads = []
        
        for idx, point in enumerate(scroll_res[:10]):  # İlk 10 point
            if point.payload:
                all_fields.update(point.payload.keys())
                sample_payloads.append({
                    'id': point.id,
                    'payload': point.payload
                })
        
        # Sonuçları göster
        print("=" * 70)
        print("METADATA FIELD'LARI")
        print("=" * 70)
        
        if not all_fields:
            print("❌ Hiç metadata field'ı bulunamadı!")
            print("   Point'ler boş payload'a sahip.")
        else:
            print(f"✅ Toplam {len(all_fields)} farklı field bulundu:\n")
            for field, count in all_fields.most_common():
                print(f"  • {field:30s} ({count} point'te var)")
        
        # Örnek payload'ları göster
        print("\n" + "=" * 70)
        print("ÖRNEK PAYLOAD'LAR (İlk 3 point)")
        print("=" * 70)
        
        for idx, sample in enumerate(sample_payloads[:3], 1):
            print(f"\n{idx}. Point ID: {sample['id']}")
            print(f"   Payload keys: {list(sample['payload'].keys())}")
            
            # Dosya adı field'larını kontrol et
            filename_fields = [
                'Mevzuat_Adi', 'Dosya_Adi', 'filename', 'file_name',
                'Mevzuat Adı', 'Dosya Adı', 'name', 'title'
            ]
            
            found_filename = None
            for field in filename_fields:
                if field in sample['payload']:
                    found_filename = sample['payload'][field]
                    print(f"   ✅ Dosya adı bulundu: {field} = '{found_filename}'")
                    break
            
            if not found_filename:
                print(f"   ❌ Dosya adı field'ı bulunamadı!")
                print(f"   📋 Mevcut field'lar: {list(sample['payload'].keys())}")
                # İlk birkaç field'ın değerini göster
                for key in list(sample['payload'].keys())[:3]:
                    value = str(sample['payload'][key])[:100]
                    print(f"      • {key}: {value}...")
        
        # Özet
        print("\n" + "=" * 70)
        print("ÖZET")
        print("=" * 70)
        
        # Dosya adı field'larını kontrol et
        filename_fields_found = []
        for field in ['Mevzuat_Adi', 'Dosya_Adi', 'filename', 'file_name', 'Mevzuat Adı', 'Dosya Adı']:
            if field in all_fields:
                filename_fields_found.append(field)
        
        if filename_fields_found:
            print(f"✅ Dosya adı field'ları bulundu: {', '.join(filename_fields_found)}")
            print(f"💡 Duplicate kontrolü bu field'ları kullanabilir.")
        else:
            print(f"❌ Dosya adı field'ı bulunamadı!")
            print(f"⚠️  Duplicate kontrolü ÇALIŞMAYACAK!")
            print(f"\n💡 Çözüm:")
            print(f"   1. PDF yüklerken metadata eklendiğinden emin olun")
            print(f"   2. Veya mevcut point'lere metadata ekleyin")
            print(f"   3. Veya collection'ı sıfırdan oluşturun")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
