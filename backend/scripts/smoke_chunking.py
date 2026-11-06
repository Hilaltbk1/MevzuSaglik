"""Ön işleme + chunker kontrolü (Qdrant/LLM gerekmez).

Çalıştır:
    python -m backend.scripts.smoke_chunking
"""
import json
from collections import Counter

from backend.preprocessing.preprocessing import file_path, flatten_mevzuat_object, verify_flatten
from backend.services.chunking11 import build_chunks, doc_key_for

with open(file_path, encoding="utf-8") as f:
    data = json.load(f)

kinds, flag_count, sizes = Counter(), Counter(), []

for i, d in enumerate(data):
    name   = d.get("Mevzuat Adı", f"belge{i}")
    flat   = flatten_mevzuat_object(d)
    rep    = verify_flatten(d, flat)
    meta   = {
        "Mevzuat_Adi":   name,
        "Mevzuat_Turu":  d.get("Mevzuat Türü", ""),
        "access_scope":  "public",
    }
    chunks = build_chunks(flat, meta, doc_key=doc_key_for(name, str(i)))
    flags  = chunks[0].metadata.get("review_flags", []) if chunks else ["bos_cikti"]

    kinds.update(c.metadata["kind"] for c in chunks)
    sizes += [len(c.text) for c in chunks]
    flag_count.update(flags)

    if rep["missing_numbers"] or flags or rep["source_table_rows"] != rep["output_table_rows"]:
        print(
            f"[İNCELE] {name}: "
            f"eksik_sayı={rep['missing_numbers'][:8]} "
            f"tablo_satır={rep['source_table_rows']}->{rep['output_table_rows']} "
            f"bayrak={flags}"
        )

print(f"\nbelge={len(data)} chunk={len(sizes)} türler={dict(kinds)}")
if sizes:
    print(f"chunk uzunluğu: min={min(sizes)} ort={sum(sizes)//len(sizes)} maks={max(sizes)}")
print("bayrak dağılımı:", dict(flag_count) or "yok")
