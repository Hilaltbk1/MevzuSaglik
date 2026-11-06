
import re
import shutil
import pandas as pd

from pathlib import Path
from difflib import SequenceMatcher
from pypdf import PdfReader
from docx import Document


# ==================================================
# 1. DOSYA YOLLARI
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

RAPOR_DOSYASI = BASE_DIR / "chunk_inceleme_raporu.csv"

HEDEF_KLASOR = BASE_DIR / "sorunlu_belgeler"

CIKTI_DOSYASI = BASE_DIR / "9_sorunlu_mevzuat.csv"

BULMA_RAPORU = BASE_DIR / "belge_bulma_sonucu.csv"

# Klasör yoksa otomatik oluştur
HEDEF_KLASOR.mkdir(parents=True, exist_ok=True)

UZANTILAR = {".pdf", ".docx", ".txt", ".md"}


# ==================================================
# 2. METİN NORMALİZASYONU
# ==================================================

def normalize(metin):
    metin = str(metin).lower()

    cevir = str.maketrans({
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c"
    })

    metin = metin.translate(cevir)
    metin = re.sub(r"[^a-z0-9\s]", " ", metin)

    return " ".join(metin.split())


# ==================================================
# 3. BELGE İSMİ BENZERLİĞİNİ HESAPLA
# ==================================================

def benzerlik_hesapla(belge_adi, dosya_adi):

    hedef = normalize(belge_adi)
    aday = normalize(dosya_adi)

    if not hedef or not aday:
        return 0

    oran = SequenceMatcher(
        None, hedef, aday
    ).ratio()

    hedef_kelimeler = set(hedef.split())
    aday_kelimeler = set(aday.split())

    ortak = hedef_kelimeler.intersection(aday_kelimeler)

    kelime_orani = (
        len(ortak) / len(hedef_kelimeler)
        if hedef_kelimeler else 0
    )

    return max(oran, kelime_orani)


# ==================================================
# 4. PDF METNİNİ OKU
# ==================================================

def pdf_oku(dosya_yolu):

    reader = PdfReader(str(dosya_yolu))

    sayfalar = []

    for sayfa_no, sayfa in enumerate(reader.pages, start=1):

        metin = sayfa.extract_text() or ""

        sayfalar.append(
            f"\n--- SAYFA {sayfa_no} ---\n{metin}"
        )

    return "\n".join(sayfalar)


# ==================================================
# 5. DOCX METNİNİ OKU
# ==================================================

def docx_oku(dosya_yolu):

    doc = Document(str(dosya_yolu))

    paragraflar = [
        p.text for p in doc.paragraphs
        if p.text.strip()
    ]

    tablolar = []

    for tablo in doc.tables:

        for satir in tablo.rows:

            hucreler = [
                hucre.text.strip()
                for hucre in satir.cells
            ]

            tablolar.append(" | ".join(hucreler))

    return "\n".join(paragraflar + tablolar)


# ==================================================
# 6. DOSYA TÜRÜNE GÖRE METİN ÇIKAR
# ==================================================

def metin_oku(dosya_yolu):

    uzanti = dosya_yolu.suffix.lower()

    if uzanti == ".pdf":
        return pdf_oku(dosya_yolu)

    elif uzanti == ".docx":
        return docx_oku(dosya_yolu)

    elif uzanti in [".txt", ".md"]:
        return dosya_yolu.read_text(
            encoding="utf-8",
            errors="replace"
        )

    raise ValueError(f"Desteklenmeyen dosya: {uzanti}")


# ==================================================
# 7. RAPORU OKU
# ==================================================

if not RAPOR_DOSYASI.exists():
    raise FileNotFoundError(
        f"İnceleme raporu bulunamadı: {RAPOR_DOSYASI}"
    )

rapor = pd.read_csv(
    RAPOR_DOSYASI,
    encoding="utf-8-sig"
)

gerekli_sutunlar = {"needs_review", "baslik"}

eksik = gerekli_sutunlar - set(rapor.columns)

if eksik:
    raise ValueError(
        f"Rapor CSV'sinde eksik sütunlar var: {eksik}"
    )

sorunlular = rapor[
    rapor["needs_review"].astype(str).str.strip().str.lower()
    .isin(["true", "1", "yes"])
]

print(f"\nSorunlu belge sayısı: {len(sorunlular)}")


# ==================================================
# 8. PROJEDEKİ BELGELERİ TARA
# ==================================================

print("\nProje klasöründeki belgeler taranıyor...")

dosyalar = []

for dosya in BASE_DIR.rglob("*"):

    if not dosya.is_file():
        continue

    if dosya.suffix.lower() not in UZANTILAR:
        continue

    # Sanal ortam, Git ve hedef klasörü tarama
    if any(
        parca.lower() in {
            ".venv", "venv", ".git",
            "node_modules", "__pycache__"
        }
        for parca in dosya.parts
    ):
        continue

    if HEDEF_KLASOR in dosya.parents:
        continue

    if dosya in {RAPOR_DOSYASI, CIKTI_DOSYASI, BULMA_RAPORU}:
        continue

    dosyalar.append(dosya)

print(f"Bulunan dosya sayısı: {len(dosyalar)}")


# ==================================================
# 9. SORUNLU BELGELERİ BUL VE KOPYALA
# ==================================================

bulma_sonuclari = []
csv_sonuclari = []

for _, belge in sorunlular.iterrows():

    belge_adi = str(belge["baslik"]).strip()

    print(f"\nAranıyor: {belge_adi}")

    adaylar = []

    for dosya in dosyalar:

        skor = benzerlik_hesapla(
            belge_adi,
            dosya.stem
        )

        adaylar.append((skor, dosya))

    adaylar.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not adaylar or adaylar[0][0] < 0.55:

        print("[BULUNAMADI] Güvenilir eşleşme yok.")

        bulma_sonuclari.append({
            "belge": belge_adi,
            "durum": "Bulunamadı",
            "dosya": ""
        })

        continue

    en_iyi_skor, kaynak = adaylar[0]

    # İki aday birbirine çok yakınsa yanlış dosya seçme
    if (
        len(adaylar) > 1
        and en_iyi_skor - adaylar[1][0] < 0.08
    ):

        print("[KARARSIZ] Birden fazla olası dosya var.")

        bulma_sonuclari.append({
            "belge": belge_adi,
            "durum": "Manuel kontrol gerekli",
            "dosya": f"{kaynak.name} / {adaylar[1][1].name}"
        })

        continue

    # Dosyayı sorunlu_belgeler klasörüne kopyala
    hedef = HEDEF_KLASOR / kaynak.name

    try:

        shutil.copy2(kaynak, hedef)

        print(f"[KOPYALANDI] {kaynak.name}")

        tam_metin = metin_oku(hedef)

        if not tam_metin.strip():

            durum = "Metin çıkarılamadı (OCR gerekebilir)"

        else:

            durum = "Kopyalandı ve metin çıkarıldı"

        csv_sonuclari.append({

            "kayit_no": belge.get("kayit_no", ""),
            "belge_adi": belge_adi,
            "belge_turu": belge.get("mevzuat_turu", ""),
            "yapi": belge.get("yapi", ""),
            "sorun": belge.get("bayraklar", ""),
            "dosya_adi": kaynak.name,
            "eslesme_skoru": round(en_iyi_skor, 3),
            "durum": durum,
            "tam_metin": tam_metin

        })

        bulma_sonuclari.append({
            "belge": belge_adi,
            "durum": durum,
            "dosya": str(kaynak)
        })

    except Exception as hata:

        print(f"[HATA] {kaynak.name}: {hata}")

        bulma_sonuclari.append({
            "belge": belge_adi,
            "durum": f"Hata: {hata}",
            "dosya": str(kaynak)
        })


# ==================================================
# 10. CSV DOSYALARINI KAYDET
# ==================================================

pd.DataFrame(bulma_sonuclari).to_csv(
    BULMA_RAPORU,
    index=False,
    encoding="utf-8-sig"
)

if csv_sonuclari:

    pd.DataFrame(csv_sonuclari).to_csv(
        CIKTI_DOSYASI,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n================================")
    print("İŞLEM TAMAMLANDI")
    print("================================")

    print(f"Metni çıkarılan/kaydedilen: {len(csv_sonuclari)}")
    print(f"Dosya bulma raporu: {BULMA_RAPORU}")
    print(f"Mevzuat CSV: {CIKTI_DOSYASI}")
    print(f"Belge klasörü: {HEDEF_KLASOR}")

else:

    print("\nHiçbir belgenin metni CSV'ye kaydedilemedi.")

print("\nSonuçlar kontrol edilmeli.")
