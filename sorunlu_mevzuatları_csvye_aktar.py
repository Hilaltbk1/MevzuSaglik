
import json
import re
import unicodedata
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# DOSYA YOLLARI
# --------------------------------------------------

JSON_KLASORU = Path("backend/data/Json")
RAPOR_DOSYASI = Path("chunk_inceleme_raporu.csv")
CIKTI_DOSYASI = Path("9_sorunlu_mevzuat.csv")

JSON_DOSYALARI = [
    JSON_KLASORU / "islenmis_mevzuat_verileri.json",
    JSON_KLASORU / "islenmis_mevzuat_verileri_duzeltilmis.json",
    JSON_KLASORU / "mevzuat_verileri.json",
]

# --------------------------------------------------
# BAŞLIKLARI NORMALLEŞTİR
# --------------------------------------------------

def normalize(metin):
    metin = str(metin).lower()

    turkce_harfler = str.maketrans({
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c"
    })

    metin = metin.translate(turkce_harfler)
    metin = unicodedata.normalize("NFKD", metin)

    metin = "".join(
        karakter for karakter in metin
        if not unicodedata.combining(karakter)
    )

    metin = re.sub(r"[^a-z0-9]+", " ", metin)

    return " ".join(metin.split())


# --------------------------------------------------
# JSON DOSYALARINI OKU
# --------------------------------------------------

tum_belgeler = []

for json_dosyasi in JSON_DOSYALARI:

    if not json_dosyasi.exists():
        print("Dosya bulunamadı:", json_dosyasi)
        continue

    with open(json_dosyasi, "r", encoding="utf-8") as f:
        kayitlar = json.load(f)

    for kayit in kayitlar:

        metadata = kayit.get("metadata", {})

        mevzuat_adi = metadata.get("Mevzuat_Adi", "")
        metin = kayit.get("page_content", "")

        if not mevzuat_adi or not metin:
            continue

        tum_belgeler.append({
            "baslik_normalize": normalize(mevzuat_adi),
            "baslik": mevzuat_adi,
            "metin": metin,
            "mevzuat_turu": metadata.get("Mevzuat_Türü", ""),
            "kaynak_json": json_dosyasi.name
        })

print("JSON kayıtları yüklendi:", len(tum_belgeler))


# --------------------------------------------------
# İNCELEME RAPORUNU OKU
# --------------------------------------------------

rapor = pd.read_csv(
    RAPOR_DOSYASI,
    encoding="utf-8-sig"
)

sorunlular = rapor[
    rapor["needs_review"].astype(str).str.lower().isin(
        ["true", "1"]
    )
]

print("Sorunlu belge sayısı:", len(sorunlular))


# --------------------------------------------------
# 9 BELGEYİ BUL VE CSV'YE HAZIRLA
# --------------------------------------------------

sonuclar = []
bulunamayanlar = []

for _, satir in sorunlular.iterrows():

    aranan_baslik = str(satir["baslik"])
    aranan_normalize = normalize(aranan_baslik)

    eslesenler = [
        belge for belge in tum_belgeler
        if belge["baslik_normalize"] == aranan_normalize
    ]

    if not eslesenler:
        print("[BULUNAMADI]", aranan_baslik)
        bulunamayanlar.append(aranan_baslik)
        continue

    # JSON_DOSYALARI listesindeki öncelik sırasına göre seç.
    secilen = eslesenler[0]

    sonuc = {
        "kayit_no": satir.get("kayit_no", ""),
        "baslik": aranan_baslik,
        "mevzuat_turu": satir.get("mevzuat_turu", ""),
        "kaynak_json": secilen["kaynak_json"],
        "metin_uzunlugu": len(secilen["metin"]),
        "bayraklar": satir.get("bayraklar", ""),
        "page_content": secilen["metin"]
    }

    sonuclar.append(sonuc)

    print(
        "[BULUNDU]",
        aranan_baslik,
        "| Karakter:",
        len(secilen["metin"]),
        "| Kaynak:",
        secilen["kaynak_json"]
    )


# --------------------------------------------------
# CSV DOSYASINI OLUŞTUR
# --------------------------------------------------

if sonuclar:

    df = pd.DataFrame(sonuclar)

    df.to_csv(
        CIKTI_DOSYASI,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nCSV başarıyla oluşturuldu:", CIKTI_DOSYASI)
    print("Aktarılan belge sayısı:", len(sonuclar))

else:
    print("\nHiçbir belge CSV'ye aktarılamadı.")


if bulunamayanlar:
    print("\nBulunamayan belgeler:")
    for baslik in bulunamayanlar:
        print("-", baslik)

print("\nİşlem tamamlandı.")
