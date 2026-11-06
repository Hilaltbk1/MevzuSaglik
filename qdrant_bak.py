import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()
client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])

for c in client.get_collections().collections:
    n = client.count(c.name).count
    print(f"\nKoleksiyon: {c.name} | kayıt sayısı: {n}")
    pts, _ = client.scroll(c.name, limit=3, with_payload=True, with_vectors=False)
    for p in pts:
        print(" id:", p.id)
        for k, v in p.payload.items():
            print(f"   {k}: {str(v)[:120]}")