"""""
Chunk'lama doğrulama raporu (Qdrant'a ya da API'ye dokunmaz).

  python -m backend.scripts.chunk_report
  python -m backend.scripts.chunk_report --json backend/data/Json/islenmis_mevzuat_verileri_duzeltilmis.json

Çıktı: chunk_inceleme_raporu.csv  → needs_review=True olan belgeleri elle kontrol edin.
"""
from __future__ import annotations
import argparse, csv, json, statistics
from collections import Counter

from backend.services.chunking11 import build_chunks, doc_key_for, detect_structure

DEFAULT_JSON = "backend/data/Json/islenmis_mevzuat_verileri_duzeltilmis.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=DEFAULT_JSON)
    ap.add_argument("--out", default="chunk_inceleme_raporu.csv")
    a = ap.parse_args()

    docs = json.load(open(a.json, encoding="utf-8"))
    rows, kinds, flag_counter = [], Counter(), Counter()
    total_chunks, sizes = 0, []
    for i, d in enumerate(docs):
        meta = d.get("metadata", {})
        title = meta.get("Mevzuat_Adi", f"doc{i}")
        tur = meta.get("Mevzuat_Türü", "")
        chunks = build_chunks(d["page_content"], {"Mevzuat_Adi": title, "Mevzuat_Türü": tur},
                              doc_key=doc_key_for(title, str(i)))
        prof = detect_structure(d["page_content"], tur)
        flags = chunks[0].metadata.get("review_flags", []) if chunks else ["bos_cikti"]
        kinds[prof["kind"]] += 1
        flag_counter.update(flags)
        total_chunks += len(chunks)
        sizes += [len(c.text) for c in chunks]
        rows.append([i, title, tur, prof["kind"], prof["length"], prof["madde_count"],
                     prof["madde_gaps"], prof["heading_count"], len(chunks),
                     bool(flags), "|".join(flags)])

    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["kayit_no", "baslik", "mevzuat_turu", "yapi", "uzunluk", "madde_sayisi",
                    "madde_atlama", "baslik_sayisi", "chunk_sayisi", "needs_review", "bayraklar"])
        w.writerows(rows)

    print(f"Belge: {len(docs)} | chunk: {total_chunks} | ort. boyut: {statistics.mean(sizes):.0f} | max: {max(sizes)}")
    print("Yapı dağılımı:", dict(kinds))
    print("Bayraklar:", dict(flag_counter))
    print("İncelenecek belge:", sum(1 for r in rows if r[9]), "→", a.out)


if __name__ == "__main__":
    main()
