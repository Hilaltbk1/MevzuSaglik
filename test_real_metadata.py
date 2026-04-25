#!/usr/bin/env python3
"""
Qdrant'taki gerçek metadata yapısını gösterir.
İlk 5 point'in tam payload'ını yazdırır.
"""

import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
COLLECTION_NAME = "mevzu_saglik_docs"

def main():
    print("=" * 80)
    print("QDRANT GERÇEK METADATA YAPISI")
    print("=" * 80)
    
    client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY, timeout=30)
    
    if not client.collection_exists(COLLECTION_NAME):
        print(f"❌ Collection '{COLLECTION_NAME}' bulunamadı!")
        return
    
    print(f"\n📚 Collection '{COLLECTION_NAME}' taranıyor...\n")
    
    scroll_res, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=5,  # İlk 5 point
        with_payload=True,
    )
    
    print(f"✅ {len(scroll_res)} point alındı\n")
    print("=" * 80)
    
    for idx, point in enumerate(scroll_res, 1):
        print(f"\n📦 POINT {idx}")
        print(f"   ID: {point.id}")
        print(f"   Payload Keys: {list(point.payload.keys())}")
        print(f"\n   📋 TAM PAYLOAD:")
        print(json.dumps(point.payload, indent=6, ensure_ascii=False))
        print("\n" + "-" * 80)
    
    # Dosya adı tespiti
    print("\n" + "=" * 80)
    print("DOSYA ADI TESPİTİ")
    print("=" * 80)
    
    scroll_res, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True,
    )
    
    found_files = set()
    
    for point in scroll_res:
        if point.payload:
            filename = None
            
            # Root level
            filename = (
                point.payload.get("Mevzuat_Adi") or
                point.payload.get("Dosya_Adi") or
                point.payload.get("filename") or
                point.payload.get("file_name")
            )
            
            # Nested metadata
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
                found_files.add(filename)
    
    print(f"\n✅ {len(found_files)} benzersiz dosya bulundu:")
    for idx, fname in enumerate(sorted(found_files)[:10], 1):
        print(f"   {idx}. {fname}")
    
    if len(found_files) > 10:
        print(f"   ... ve {len(found_files) - 10} dosya daha")

if __name__ == "__main__":
    main()
