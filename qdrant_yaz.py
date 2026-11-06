"""
Kullanım:
  py qdrant_yaz.py            -> SADECE RAPOR (Qdrant'a hiçbir şey yazmaz)
  py qdrant_yaz.py --dene     -> sadece 1 belgeyi (Hasta Hakları Yönetmeliği) yazar
  py qdrant_yaz.py --yaz      -> eşleşen tüm parçaları yazar (önce yedek alır)
Gerekli: QDRANT_URL ve QDRANT_API_KEY ortam değişkenleri, aynı klasörde kategori_eslemesi.json
"""
import os, re, sys, json, csv, hashlib
from bisect import bisect_right
from collections import defaultdict, Counter

COL = "mevzu_saglik_docs"
DIR = r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\backend\data\Json"
ORIJINAL = os.path.join(DIR, "islenmis_mevzuat_verileri.json")
DUZELTILMIS = os.path.join(DIR, "islenmis_mevzuat_verileri_duzeltilmis.json")
DENE_KAYIT = 125  # Hasta Hakları Yönetmeliği

norm = lambda s: re.sub(r"\s+", " ", s or "").strip()


def build_index(texts):
    starts, pos, parts = [], 0, []
    for t in texts:
        starts.append(pos)
        parts.append(t)
        pos += len(t) + 1
    return "\x00".join(parts), starts


def find_records(big, starts, chunk, snip=60):
    t = norm(chunk)
    if len(t) < 30:
        return set()
    cands = None
    for frac in (0.5, 0.25, 0.75):
        n = min(snip, len(t))
        i = max(0, min(len(t) - n, int(len(t) * frac) - n // 2))
        needle = t[i:i + n]
        s, p, c = set(), big.find(needle), 0
        while p != -1 and c < 50:
            s.add(bisect_right(starts, p) - 1)
            p = big.find(needle, p + 1)
            c += 1
        if not s:
            continue
        cands = s if cands is None else ((cands & s) or cands)
        if len(cands) == 1:
            break
    return cands or set()


def main():
    yaz = "--yaz" in sys.argv
    dene = "--dene" in sys.argv
    from qdrant_client import QdrantClient

    orj = json.load(open(ORIJINAL, encoding="utf-8"))
    dz = json.load(open(DUZELTILMIS, encoding="utf-8"))
    esleme = json.load(open("kategori_eslemesi.json", encoding="utf-8"))
    ver = esleme["taxonomy_version"]
    docs = esleme["documents"]
    texts = [norm(d["page_content"]) for d in orj]
    hashes = [hashlib.sha1(t.encode("utf-8")).hexdigest()[:16] for t in texts]
    titles = [d["metadata"].get("Mevzuat_Adi", "") for d in dz]
    big, starts = build_index(texts)
    print("Belge sayısı:", len(texts), "| indeks boyutu: %.1f MB" % (len(big) / 1e6))

    client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=120)
    chunks, offset = [], None
    while True:
        pts, offset = client.scroll(COL, limit=500, offset=offset, with_payload=True, with_vectors=False)
        chunks += pts
        if offset is None:
            break
    print("Qdrant parça sayısı:", len(chunks))

    atanan = defaultdict(list)       # kayit_no -> [point id]
    yok, belirsiz = [], []
    for k, p in enumerate(chunks):
        if k and k % 2000 == 0:
            print("  eşleştirildi:", k)
        c = find_records(big, starts, p.payload.get("page_content", ""))
        if not c:
            yok.append(p.id); continue
        if len(c) > 1:
            imza = {docs[str(r)]["primary"] for r in c}
            if len(imza) > 1:
                belirsiz.append((p.id, sorted(c))); continue
        atanan[min(c)].append(p.id)

    print("\nEşleşen parça:", sum(len(v) for v in atanan.values()),
          "| eşleşmeyen:", len(yok), "| belirsiz (farklı kategorili):", len(belirsiz))
    print("Parçası bulunan belge:", len(atanan), "/", len(texts))
    print("Hiç parçası olmayan kayit_no:", [i for i in range(len(texts)) if i not in atanan])
    if belirsiz:
        print("Belirsiz örnekler:", belirsiz[:5])

    with open("chunk_eslesme_raporu.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["kayit_no", "baslik", "ana_kategori", "parca_sayisi"])
        for i in range(len(texts)):
            w.writerow([i, titles[i], docs[str(i)]["primary"], len(atanan.get(i, []))])
    print("chunk_eslesme_raporu.csv yazıldı")

    if not (yaz or dene):
        print("\n(Rapor modu: Qdrant'a hiçbir şey yazılmadı.)")
        return

    hedef = {DENE_KAYIT: atanan[DENE_KAYIT]} if dene else dict(atanan)
    if dene and DENE_KAYIT not in atanan:
        print("Deneme belgesi için parça bulunamadı, durdum."); return

    yedek = {str(p.id): (p.payload.get("metadata") or {}) for p in chunks}
    json.dump(yedek, open("qdrant_metadata_yedek.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("Yedek alındı: qdrant_metadata_yedek.json")

    for kayit, ids in hedef.items():
        d = docs[str(kayit)]
        payload = {"Mevzuat_Adi": titles[kayit], "topics": d["topics"], "primary_topic": d["primary"],
                   "taxonomy_version": ver, "topic_status": "draft", "content_hash": hashes[kayit]}
        for i in range(0, len(ids), 500):
            client.set_payload(COL, payload=payload, points=ids[i:i + 500], key="metadata", wait=True)
    print("Yazıldı:", len(hedef), "belge,", sum(len(v) for v in hedef.values()), "parça")

    ornek = client.retrieve(COL, ids=[list(hedef.values())[0][0]], with_payload=True)[0]
    print("Örnek kayıt metadata:", ornek.payload.get("metadata"))


if __name__ == "__main__":
    main()