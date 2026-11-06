"""
Backfill ve kategori doğrulama scripti.
Çalıştır: python tests/verify_backfill.py
"""
import os, sys
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    docs_ready = c.execute(text("SELECT COUNT(*) FROM documents WHERE status='ready'")).scalar()
    docs_total = c.execute(text("SELECT COUNT(*) FROM documents")).scalar()
    cats       = c.execute(text("SELECT COUNT(*) FROM category")).scalar()
    doccats    = c.execute(text("SELECT COUNT(*) FROM document_category")).scalar()

print(f"documents (ready/toplam): {docs_ready} / {docs_total}")
print(f"category satirlari      : {cats}")
print(f"document_category       : {doccats}")

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(
    url=os.getenv("QDRANT_HOST", "").strip(),
    api_key=os.getenv("QDRANT_API_KEY", "").strip(),
    timeout=30,
)

public_count = client.count(
    collection_name="mevzu_saglik_docs",
    count_filter=Filter(
        must=[FieldCondition(key="metadata.access_scope", match=MatchValue(value="public"))]
    ),
)
print(f"Qdrant public parca     : {public_count.count}")

ids = set()
offset = None
while True:
    pts, offset = client.scroll(
        "mevzu_saglik_docs", limit=500, offset=offset,
        with_payload=True, with_vectors=False,
    )
    for p in pts:
        did = (p.payload.get("metadata") or {}).get("document_id")
        if did:
            ids.add(did)
    if offset is None:
        break

print(f"Qdrant benzersiz doc_id : {len(ids)}")

print()
PASS = FAIL = 0
def chk(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  OK  {msg}")
    else:
        FAIL += 1; print(f"  FAIL {msg}")

chk(docs_ready > 100,    f"documents ready > 100 ({docs_ready})")
chk(cats >= 10,          f"category >= 10 satir ({cats})")
chk(doccats > 0,         f"document_category baglantisi var ({doccats})")
chk(public_count.count > 15000, f"Qdrant public parca > 15000 ({public_count.count})")
chk(len(ids) > 100,      f"Qdrant benzersiz document_id > 100 ({len(ids)})")
chk(len(ids) <= docs_total, f"Qdrant doc_id <= DB toplam belge")

print(f"\nSonuc: {PASS} gecti, {FAIL} basarisiz")
sys.exit(0 if FAIL == 0 else 1)
