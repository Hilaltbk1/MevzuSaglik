
import json
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

KLASOR = Path("backend/data/Json")

JSON_DOSYALARI = [
    KLASOR / "islenmis_mevzuat_verileri.json",
    KLASOR / "islenmis_mevzuat_verileri_duzeltilmis.json",
    KLASOR / "mevzuat_verileri.json",
]

RAPOR = Path("chunk_inceleme_raporu.csv")

def normalize(metin):
    metin = str(metin).lower()
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(
        c for c in metin
        if not unicodedata.combining(c)
    )
    metin = re.sub(r"[^a-z0-9]+", " ", metin)
    return " ".join(metin.split())


# Sorunlu başlıkları oku
import pandas as pd

rapor = pd.read_csv(RAPOR, encoding="utf-8-sig")
sorunlular = rapor[
    rapor["needs_review"].astype(str).str.lower().isin(["true", "1"])
]

# Üç JSON dosyasını tara
tum_belgeler = []

for dosya in JSON_DOSYALARI:
    if not dosya.exists():
        print(f"\nDOSYA BULUNAMADI: {dosya}")
        continue

    with open(dosya, "r", encoding="utf-8") as f:
        veriler = json.load(f)

    print(f"\n{dosya.name}: {len(veriler)} kayıt")

    for belge in veriler:
        metadata = belge.get("metadata", {})
        ad = metadata.get("Mevzuat_Adi", "")

        tum_belgeler.append({
            "dosya": dosya.name,
            "ad": ad,
            "metin": belge.get("page_content", "")
        })

print("\nToplam taranan kayıt:", len(tum_belgeler))

# Eşleştirme
for _, satir in sorunlular.iterrows():
    baslik = str(satir["baslik"])
    hedef = normalize(baslik)

    adaylar = []

    for belge in tum_belgeler:
        ad = normalize(belge["ad"])

        if not ad:
            continue

        oran = SequenceMatcher(None, hedef, ad).ratio()

        adaylar.append((oran, belge))

    adaylar.sort(key=lambda x: x[0], reverse=True)

    print("\n" + "=" * 70)
    print("ARANAN:", baslik)

    if adaylar and adaylar[0][0] == 1.0:
        oran, belge = adaylar[0]
        print("KESİN EŞLEŞME:", belge["ad"])
        print("KAYNAK JSON:", belge["dosya"])
        print("METİN UZUNLUĞU:", len(belge["metin"]))
    else:
        print("KESİN EŞLEŞME YOK.")
        print("En yakın adaylar:")

        for oran, belge in adaylar[:3]:
            print(
                f"%{oran * 100:.1f} - {belge['ad']} "
                f"({belge['dosya']})"
            )
