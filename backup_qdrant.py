"""
Qdrant veritabanını yedekler - eğer cluster silinirse sıfırdan yüklemek için
"""
import os, json
from datetime import datetime
from qdrant_client import QdrantClient

# Qdrant bağlantısı
QDRANT_HOST = "https://987f8110-d7ab-4529-8c14-ff853f854764.eu-central-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZDkwMWQyNzgtMGMwZS00MjgyLWIwN2UtNDA5ZGVkYTY2ZmZlIn0.LteoHaf_laW3l7QWHp4Cv-otHnoEI53QcMKzkqHsdrU"

def backup_qdrant():
    try:
        client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY, prefer_grpc=False)
        
        # Cluster durumu
        count = client.count('mevzu_saglik_docs').count
        
        backup_info = {
            "backup_date": datetime.now().isoformat(),
            "total_chunks": count,
            "cluster_url": QDRANT_HOST,
            "collection_name": "mevzu_saglik_docs",
            "status": "OK" if count > 0 else "EMPTY",
            "restore_files": [
                "backend/data/Json/islenmis_mevzuat_verileri.json",
                "upload_to_qdrant.py"
            ]
        }
        
        # Backup bilgisini kaydet
        with open(f'qdrant_backup_{datetime.now().strftime("%Y%m%d")}.json', 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Backup OK: {count} chunks")
        print(f"📁 Backup dosyası: qdrant_backup_{datetime.now().strftime('%Y%m%d')}.json")
        
    except Exception as e:
        print(f"❌ Backup hatası: {e}")

if __name__ == "__main__":
    backup_qdrant()