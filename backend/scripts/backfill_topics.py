"""
Qdrant chunk'larına topics / primary_topic yazar.

  python -m backend.scripts.backfill_topics           # dry-run
  python -m backend.scripts.backfill_topics --apply   # yazar
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

load_dotenv()

COLLECTION = "mevzu_saglik_docs"
ROOT = Path(__file__).resolve().parents[2]
DOCS_JSON = ROOT / "backend" / "data" / "Json" / "islenmis_mevzuat_verileri.json"
CAT_JSON = ROOT / "kategori_eslesmesi.json"


def _norm(name: str) -> str:
    n = (name or "").strip()
    if n.lower().endswith(".pdf"):
        n = n[:-4]
    return " ".join(n.lower().split())


def _client() -> QdrantClient:
    return QdrantClient(
        url=os.getenv("QDRANT_HOST", "").strip(),
        api_key=os.getenv("QDRANT_API_KEY", "").strip() or None,
        prefer_grpc=False,
        timeout=300,
    )


def _title_to_topics() -> dict[str, dict]:
    docs = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    cats = json.loads(CAT_JSON.read_text(encoding="utf-8"))["documents"]
    out = {}
    for i, d in enumerate(docs):
        title = (d.get("metadata") or {}).get("Mevzuat_Adi") or ""
        info = cats.get(str(i)) or {"topics": ["genel"], "primary": "genel"}
        out[_norm(title)] = {
            "topics": info.get("topics") or ["genel"],
            "primary_topic": info.get("primary") or "genel",
        }
    return out


def _read_name(payload: dict) -> str | None:
    meta = payload.get("metadata")
    src = meta if isinstance(meta, dict) else payload
    return (
        src.get("Mevzuat_Adi") or src.get("Dosya_Adi")
        or src.get("filename") or src.get("file_name")
    )


def main(apply: bool):
    mapping = _title_to_topics()
    print(f"Eşleme: {len(mapping)} belge")

    client = _client()

    # Index (yoksa oluştur)
    for field in ("metadata.primary_topic", "metadata.topics"):
        try:
            client.create_payload_index(
                COLLECTION, field_name=field, field_schema=PayloadSchemaType.KEYWORD
            )
            print(f"index ok: {field}")
        except Exception as e:
            print(f"index skip/warn {field}: {e}")

    by_title = defaultdict(list)
    offset = None
    total = matched = 0
    while True:
        points, offset = client.scroll(
            COLLECTION, limit=256, offset=offset,
            with_payload=True, with_vectors=False,
        )
        for p in points:
            total += 1
            name = _read_name(p.payload or {})
            if not name:
                continue
            key = _norm(name)
            info = mapping.get(key)
            if not info:
                continue
            matched += 1
            by_title[key].append(p.id)
            if apply:
                # Nested metadata merge — "metadata.topics" düz key YAZMA
                meta = dict((p.payload or {}).get("metadata") or {})
                meta["topics"] = info["topics"]
                meta["primary_topic"] = info["primary_topic"]
                client.set_payload(
                    collection_name=COLLECTION,
                    payload={"metadata": meta},
                    points=[p.id],
                )
        if offset is None:
            break

    print(f"toplam chunk={total} eşleşen={matched} belge_grubu={len(by_title)}")
    if not apply:
        print("DRY-RUN. Yazmak için: --apply")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    main(args.apply)