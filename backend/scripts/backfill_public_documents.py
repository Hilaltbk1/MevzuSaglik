"""
Qdrant'taki mevcut ortak belgeleri Postgres'e kaydeder ve vektörlere
document_id + access_scope="public" etiketi yazar.

  python -m backend.scripts.backfill_public_documents            # sadece plan gösterir
  python -m backend.scripts.backfill_public_documents --apply    # gerçekten yazar

Tekrar çalıştırmak güvenlidir.
"""
from __future__ import annotations
import os
import sys
from collections import Counter, defaultdict
from dotenv import load_dotenv

load_dotenv()

# crud.py'yi import etmek yerine doğrudan Qdrant bağlantısı kur
# (langchain importlarından kaçınmak için)
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType


COLLECTION_NAME = "mevzu_saglik_docs"


def _get_qdrant_client() -> QdrantClient:
    host    = os.getenv("QDRANT_HOST", "").strip().strip('\n').strip('\r')
    api_key = os.getenv("QDRANT_API_KEY", "").strip().strip('\n').strip('\r')
    return QdrantClient(url=host, api_key=api_key, prefer_grpc=False, timeout=300)


def _get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    return Session()


def _norm(name: str) -> str:
    n = name.strip()
    if n.lower().endswith(".pdf"):
        n = n[:-4]
    return " ".join(n.lower().split())


def _read(payload: dict):
    meta   = payload.get("metadata")
    nested = isinstance(meta, dict)
    src    = meta if nested else payload
    name   = (
        src.get("Mevzuat_Adi") or src.get("Dosya_Adi") or
        src.get("filename")    or src.get("file_name") or
        src.get("Mevzuat Adı") or src.get("Dosya Adı")
    )
    return name, nested


def scan(client):
    groups = defaultdict(list)
    titles = defaultdict(Counter)
    flat = noname = total = 0
    offset = None
    while True:
        points, offset = client.scroll(
            COLLECTION_NAME, limit=256, offset=offset,
            with_payload=True, with_vectors=False,
        )
        for p in points:
            total += 1
            name, nested = _read(p.payload or {})
            if not nested:
                flat += 1
            if not name:
                noname += 1
                continue
            key = _norm(name)
            groups[key].append(p.id)
            titles[key][name.strip()] += 1
        if offset is None:
            break
    return groups, titles, total, flat, noname


def main(apply: bool):
    print("Qdrant'a bağlanılıyor...")
    client = _get_qdrant_client()

    print("Veriler taranıyor...")
    groups, titles, total, flat, noname = scan(client)
    print(
        f"Toplam parça: {total} | belge sayısı: {len(groups)} | "
        f"metadata'sı düz (nested değil): {flat} | adı bulunamayan: {noname}"
    )

    if apply and (flat or noname):
        sys.exit("DURDU: düz metadata veya adsız parça var. Önce bu sayıları kontrol et.")

    from sqlalchemy import text

    db = _get_db()
    try:
        for key, ids in sorted(groups.items()):
            title = titles[key].most_common(1)[0][0]
            if title.lower().endswith(".pdf"):
                title = title[:-4]
            title = " ".join(title.split())[:500]
            print(f"  {title[:60]:60} {len(ids):5} parça")
            if not apply:
                continue

            # PostgreSQL'e bak veya yeni kayıt ekle
            from backend.schemas.document_model import DocumentModel
            doc = db.query(DocumentModel).filter_by(access_scope="public", title=title).first()
            if not doc:
                doc = DocumentModel(
                    title=title,
                    access_scope="public",
                    status="ready",
                    document_type="Sağlık Mevzuatı",
                    chunk_count=len(ids),
                )
                db.add(doc)
                db.flush()
            else:
                doc.chunk_count = len(ids)
            db.commit()

            # Qdrant'a document_id ve access_scope yaz
            for i in range(0, len(ids), 200):
                client.set_payload(
                    COLLECTION_NAME,
                    payload={"document_id": str(doc.id), "access_scope": "public"},
                    points=ids[i:i + 200],
                    key="metadata",
                )

        if apply:
            # Index oluştur (hızlı filtreleme için)
            try:
                client.create_payload_index(
                    COLLECTION_NAME, "metadata.document_id", PayloadSchemaType.KEYWORD
                )
                client.create_payload_index(
                    COLLECTION_NAME, "metadata.access_scope", PayloadSchemaType.KEYWORD
                )
            except Exception:
                pass  # Index zaten varsa hata verir, sorun değil
            print("\nBitti.")
        else:
            print(f"\nBu sadece plandı ({len(groups)} belge listelenecek). Gerçekten yazmak için --apply ekle.")
    finally:
        db.close()


if __name__ == "__main__":
    main("--apply" in sys.argv)
