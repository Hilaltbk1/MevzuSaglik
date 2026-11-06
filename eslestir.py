import os, re, json, csv
from collections import defaultdict, Counter
from qdrant_client import QdrantClient
from dotenv import load_dotenv
load_dotenv()
COL = "mevzu_saglik_docs"
JSON_YOLU = r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\backend\data\Json\islenmis_mevzuat_verileri_duzeltilmis.json"

norm = lambda s: re.sub(r"\s+", " ", s or "").strip()

# 1) Bizim 152 belge (sıra numarası = kayit_no)
with open(JSON_YOLU, encoding="utf-8") as f:
    veri = json.load(f)
metinler = [norm(d["page_content"]) for d in veri]
yeni_baslik = [d["metadata"].get("Mevzuat_Adi", "") for d in veri]
eski_baslik = [d["metadata"].get("Mevzuat_Adi_Eski", d["metadata"].get("Mevzuat_Adi", "")) for d in veri]
turler = [d["metadata"].get("Mevzuat_Türü", "") for d in veri]

# 2) Qdrant'taki tüm parçaları oku (sadece okuma)
client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=120)
gruplar = defaultdict(list)
offset = None
while True:
    pts, offset = client.scroll(COL, limit=500, offset=offset, with_payload=True, with_vectors=False)
    for p in pts:
        md = p.payload.get("metadata", {}) or {}
        gruplar[md.get("document_id")].append((p.payload.get("page_content", ""), md))
    if offset is None:
        break

print("Toplam parça:", sum(len(v) for v in gruplar.values()))
print("Benzersiz document_id:", len(gruplar))
ilk = next(iter(gruplar.values()))[0][1]
print("metadata alanları:", list(ilk.keys()))

# 3) Her document_id için birkaç parçayı bizim belgelerde ara
satirlar, eslesen = [], defaultdict(list)
for doc_id, parcalar in gruplar.items():
    n = len(parcalar)
    secilen = [parcalar[int(i * (n - 1) / 4)] for i in range(5)] if n >= 5 else parcalar
    oy = Counter()
    for metin, md in secilen:
        t = norm(metin)
        if len(t) < 80:
            continue
        orta = len(t) // 2
        parca = t[orta - 40: orta + 40]
        for k, m in enumerate(metinler):
            if parca in m:
                oy[k] += 1
    q_baslik = parcalar[0][1].get("Mevzuat_Adi", "")
    q_tur = parcalar[0][1].get("Mevzuat_Türü", "")
    if not oy:
        kayit, durum = "", "ESLESMEDI"
    else:
        en_cok = max(oy.values())
        adaylar = [k for k, v in oy.items() if v == en_cok]
        if len(adaylar) > 1:  # eşitlik: eski başlık ve türe göre ayır
            dar = [k for k in adaylar if eski_baslik[k] == q_baslik and turler[k] == q_tur]
            adaylar = dar or adaylar
        if len(adaylar) == 1:
            kayit, durum = adaylar[0], "ESLESTI"
            eslesen[kayit].append(doc_id)
        else:
            kayit, durum = "", "BELIRSIZ:" + "/".join(map(str, adaylar))
    satirlar.append([doc_id, n, q_baslik, q_tur, kayit, yeni_baslik[kayit] if kayit != "" else "", durum])

with open("eslesme_raporu.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["document_id", "parca_sayisi", "qdrant_baslik", "tur", "kayit_no", "yeni_baslik", "durum"])
    w.writerows(satirlar)

print("\nDurum dağılımı:", Counter(s[6].split(":")[0] for s in satirlar))
print("Eşleşmeyen/belirsiz document_id'ler:")
for s in satirlar:
    if s[6] != "ESLESTI":
        print(" ", s[0], "|", s[3], "|", s[2][:50], "|", s[6])
yok = [k for k in range(len(veri)) if k not in eslesen]
print("\nQdrant'ta karşılığı bulunamayan kayit_no'lar:", yok)
coklu = {k: v for k, v in eslesen.items() if len(v) > 1}
print("Birden fazla document_id'ye eşleşen kayit_no'lar:", {k: len(v) for k, v in coklu.items()})
print("\neslesme_raporu.csv yazıldı")  