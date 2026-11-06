import os
from collections import Counter
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient

e = create_engine(os.environ["DATABASE_URL"])
with e.connect() as c:
    rows = c.execute(text(
        "select id, title, document_type, access_scope, status, chunk_count, content_hash, source_url "
        "from documents order by title")).mappings().all()

print("documents satır sayısı:", len(rows))
print("status dağılımı:", Counter(r["status"] for r in rows))
print("access_scope dağılımı:", Counter(r["access_scope"] for r in rows))
print("chunk_count toplamı:", sum(r["chunk_count"] or 0 for r in rows))
print("content_hash dolu:", sum(1 for r in rows if r["content_hash"]), "| source_url dolu:", sum(1 for r in rows if r["source_url"]))

print("\nİlk 8 satır:")
for r in rows[:8]:
    print(" ", str(r["id"])[:8], "|", (r["title"] or "")[:55], "|", r["document_type"], "|", r["status"], "|", r["chunk_count"])

# Qdrant'taki document_id'lerle karşılaştır
client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=120)
q_ids, offset = Counter(), None
while True:
    pts, offset = client.scroll("mevzu_saglik_docs", limit=500, offset=offset, with_payload=["metadata"], with_vectors=False)
    for p in pts:
        q_ids[(p.payload.get("metadata") or {}).get("document_id")] += 1
    if offset is None:
        break

db_ids = {str(r["id"]) for r in rows}
print("\nQdrant'ta benzersiz document_id:", len(q_ids))
print("Hem Qdrant'ta hem documents'ta olan:", len(db_ids & set(q_ids)))
print("Sadece Qdrant'ta olan:", len(set(q_ids) - db_ids))
print("Sadece documents'ta olan:", len(db_ids - set(q_ids)))

farkli = [(str(r["id"])[:8], r["chunk_count"], q_ids.get(str(r["id"]))) for r in rows
          if str(r["id"]) in q_ids and r["chunk_count"] != q_ids[str(r["id"])]]
print("chunk_count Qdrant ile uyuşmayan belge sayısı:", len(farkli), farkli[:5])