"""
Kullanım:
  py kimlik_duzelt.py          -> SADECE RAPOR (hiçbir şey yazmaz)
  py kimlik_duzelt.py --dene   -> sadece Hasta Hakları Yönetmeliği için PostgreSQL + Qdrant yazar
  py kimlik_duzelt.py --yaz    -> tüm belgeler için yazar (önce yedek alır)
Gerekli: qdrant_yaz.py ve kategori_eslemesi.json aynı klasörde; QDRANT_URL, QDRANT_API_KEY, DATABASE_URL tanımlı.
"""
import os, sys, json, uuid, hashlib
from collections import defaultdict, Counter
from qdrant_yaz import build_index, find_records, norm, ORIJINAL, DUZELTILMIS, COL, DENE_KAYIT

ACIKLAMA = {
 "halk_sagligi": "Bulaşıcı ve bulaşıcı olmayan hastalıklar, salgın, aşı, tarama, kayıt sistemleri",
 "anne_cocuk_uremme": "Gebelik, doğum, bebek-çocuk izlem, nüfus planlaması",
 "beslenme_gida_su": "Beslenme programları, gıda ve su güvenliği",
 "tutun_madde": "Tütün, nargile, uyuşturucu, uçucu madde ve bağımlılık merkezleri",
 "acil_saglik": "Acil sağlık hizmetleri, ambulans, hastane öncesi hizmet",
 "hizmet_sunumu_kurumlar": "Sağlık hizmetinin örgütlenmesi, birinci basamak, kurum yapısı",
 "calisanlar_hasta_haklari": "Meslekler, atama, disiplin, etik, hasta hakları, iş sağlığı",
 "ilac_cihaz_eczacilik": "İlaç, eczane, reçete, tıbbi cihaz",
 "cevre_denetim": "Çevre sağlığı, kaplıca, mezarlık, tıbbi atık, denetime tabi yerler",
 "genel": "Emin olunmayan veya çapraz konulu belgeler",
}


def assign_ids(rec_cur, hashes, hash_row, new_id=lambda: str(uuid.uuid4())):
    """rec_cur: {kayit: Counter(mevcut_document_id)} -> {kayit: hedef_document_id}"""
    target, claimed = {}, set()
    for r in sorted(rec_cur):                      # 1) içerik hash'i daha önce yazılmışsa aynı kimlik
        d = hash_row.get(hashes[r])
        if d and d not in claimed:
            target[r] = d; claimed.add(d)
    pairs = sorted(((n, r, d) for r, cnt in rec_cur.items() if r not in target
                    for d, n in cnt.items()), key=lambda x: (-x[0], x[1]))
    for n, r, d in pairs:                          # 2) en çok parçası olan mevcut kimliği koru
        if r not in target and d not in claimed:
            target[r] = d; claimed.add(d)
    for r in sorted(rec_cur):                      # 3) kalanlara yeni kimlik
        if r not in target:
            target[r] = new_id()
    return target


def main():
    yaz, dene = "--yaz" in sys.argv, "--dene" in sys.argv
    from qdrant_client import QdrantClient
    from sqlalchemy import create_engine, text

    orj = json.load(open(ORIJINAL, encoding="utf-8"))
    dz = json.load(open(DUZELTILMIS, encoding="utf-8"))
    esleme = json.load(open("kategori_eslemesi.json", encoding="utf-8"))
    ver, docs, tax = esleme["taxonomy_version"], esleme["documents"], esleme["taxonomy"]
    texts = [norm(d["page_content"]) for d in orj]
    hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
    titles = [d["metadata"].get("Mevzuat_Adi", "") for d in dz]
    big, starts = build_index(texts)

    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(text(
            "select id::text as id, title, chunk_count, content_hash from documents")).mappings()]
    existing = {r["id"]: r for r in rows}
    hash_row = {r["content_hash"]: r["id"] for r in rows if r["content_hash"]}
    print("documents satırı:", len(rows), "| belge:", len(texts))

    client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=120)
    chunks, offset = [], None
    while True:
        pts, offset = client.scroll(COL, limit=500, offset=offset, with_payload=True, with_vectors=False)
        chunks += pts
        if offset is None:
            break
    cur = {str(p.id): str((p.payload.get("metadata") or {}).get("document_id")) for p in chunks}
    print("Qdrant parça:", len(chunks))

    atanan, yok, belirsiz = defaultdict(list), 0, 0
    for k, p in enumerate(chunks):
        if k and k % 4000 == 0:
            print("  eşleştirildi:", k)
        cands = find_records(big, starts, p.payload.get("page_content", ""))
        if not cands:
            yok += 1; continue
        if len(cands) > 1 and len({docs[str(r)]["primary"] for r in cands}) > 1:
            belirsiz += 1; continue
        atanan[min(cands)].append(str(p.id))
    print(f"Eşleşen belge: {len(atanan)}/{len(texts)} | eşleşmeyen parça: {yok} | belirsiz parça: {belirsiz}")

    kapsam = {DENE_KAYIT} if dene else set(atanan)
    rec_cur = {r: Counter(cur[i] for i in atanan[r]) for r in kapsam if r in atanan}
    target = assign_ids(rec_cur, hashes, hash_row)

    final = dict(cur)
    for r, T in target.items():
        for i in atanan[r]:
            final[i] = T
    eski_sayi, yeni_sayi = Counter(cur.values()), Counter(final.values())
    yeni_kimlik = [r for r, T in target.items() if T not in existing]
    tasinan = sum(1 for i in cur if cur[i] != final[i])
    degisen = [d for d in set(eski_sayi) | set(yeni_sayi) if eski_sayi.get(d, 0) != yeni_sayi.get(d, 0)]
    sahipsiz = [d for d in existing if d not in set(target.values())]

    print("\n--- RAPOR ---")
    print("Mevcut kimliği korunacak belge:", len(target) - len(yeni_kimlik))
    print("Yeni kimlik (yeni documents satırı) açılacak belge:", len(yeni_kimlik))
    print("Qdrant'ta document_id'si değişecek parça:", tasinan)
    print("chunk_count değişecek satır:", len(degisen))
    print("Hiçbir belgenin sahiplenmediği mevcut satır:", len(sahipsiz))
    for r in yeni_kimlik[:30]:
        print("  yeni:", r, "|", titles[r][:70], "|", len(atanan[r]), "parça")

    if not (yaz or dene):
        print("\n(Rapor modu: hiçbir şey yazılmadı.)"); return

    json.dump(rows, open("documents_yedek.json", "w", encoding="utf-8"), ensure_ascii=False, default=str)
    json.dump({str(p.id): (p.payload.get("metadata") or {}) for p in chunks},
              open("qdrant_metadata_yedek2.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("Yedekler alındı: documents_yedek.json, qdrant_metadata_yedek2.json")

    with engine.begin() as c:                       # tek işlem: hata olursa hiçbir şey kalmaz
        for slug, ad in tax.items():
            c.execute(text("insert into category(slug,name,description) values(:s,:n,:d) "
                           "on conflict (slug) do nothing"), {"s": slug, "n": ad, "d": ACIKLAMA.get(slug, "")})
        cat_id = {r.slug: r.id for r in c.execute(text("select id, slug from category"))}
        for r, T in target.items():
            p = {"id": T, "t": titles[r][:500], "h": hashes[r], "n": yeni_sayi.get(T, 0)}
            if T in existing:
                c.execute(text("update documents set title=:t, content_hash=:h, chunk_count=:n, updated_at=now() "
                               "where id=cast(:id as uuid)"), p)
            else:
                c.execute(text("insert into documents(id,title,document_type,access_scope,status,content_hash,chunk_count) "
                               "values(cast(:id as uuid),:t,'Sağlık Mevzuatı','public','ready',:h,:n)"), p)
            c.execute(text("delete from document_category where document_id=cast(:id as uuid)"), {"id": T})
            for slug in docs[str(r)]["topics"]:
                c.execute(text("insert into document_category(document_id,category_id) values(cast(:d as uuid),:c)"),
                          {"d": T, "c": cat_id[slug]})
        for d in degisen:
            if d in existing and d not in set(target.values()):
                c.execute(text("update documents set chunk_count=:n, updated_at=now() where id=cast(:id as uuid)"),
                          {"id": d, "n": yeni_sayi.get(d, 0)})
    print("PostgreSQL güncellendi.")

    for r, T in target.items():
        payload = {"document_id": T, "Mevzuat_Adi": titles[r], "topics": docs[str(r)]["topics"],
                   "primary_topic": docs[str(r)]["primary"], "taxonomy_version": ver,
                   "topic_status": "draft", "content_hash": hashes[r]}
        ids = atanan[r]
        for i in range(0, len(ids), 500):
            client.set_payload(COL, payload=payload, points=ids[i:i + 500], key="metadata", wait=True)
    print("Qdrant güncellendi.")

    with engine.connect() as c:
        print("Doğrulama -> documents:", c.execute(text("select count(*) from documents")).scalar(),
              "| chunk_count toplamı:", c.execute(text("select sum(chunk_count) from documents")).scalar(),
              "| document_category:", c.execute(text("select count(*) from document_category")).scalar())


if __name__ == "__main__":
    main()