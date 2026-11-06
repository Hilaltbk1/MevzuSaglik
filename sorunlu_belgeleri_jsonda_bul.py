
import json
import pandas as pd
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

JSON_DOSYASI = Path("backend/data/Json/islenmis_mevzuat_verileri.json")
RAPOR_DOSYASI = Path("chunk_inceleme_raporu.csv")

def normalize(metin):
    metin = str(metin).lower()
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(
        c for c in metin
        if not unicodedata.combining(c)
    )
    metin = re.sub(r"[^a-z0-9]+", " ", metin)
    return " ".join(metin.split())

# JSON kayıtlarını oku
with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
    belgeler = json.load(f)

# İnceleme raporunu oku
rapor = pd.read_csv(RAPOR_DOSYASI, encoding="utf-8-sig")

print("Rapor sütunları:", rapor.columns.tolist())

# Sorunlu kayıtları belirle
sorunlular = rapor[
    rapor["needs_review"].astype(str).str.lower().isin(["true", "1"])
]

print("\nSorunlu belge sayısı:", len(sorunlular))
print("\nJSON'daki mevzuat adları:")

for belge in belgeler[:5]:
    print("-", belge["metadata"].get("Mevzuat_Adi"))

print("\n--- EŞLEŞTİRME SONUÇLARI ---")

for _, satir in sorunlular.iterrows():
    baslik = str(satir["baslik"])
    hedef = normalize(baslik)

    adaylar = []

    for belge in belgeler:
        ad = belge.get("metadata", {}).get("Mevzuat_Adi", "")
        aday = normalize(ad)

        benzerlik = SequenceMatcher(
            None, hedef, aday
        ).ratio()

        adaylar.append((benzerlik, ad))

    adaylar.sort(reverse=True)

    print("\nAranan:", baslik)

    for puan, ad in adaylar[:3]:
        print(f"  %{puan * 100:.1f} - {ad}")
