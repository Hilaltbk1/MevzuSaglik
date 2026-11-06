import json, csv, re
from collections import Counter

DOSYA = r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\backend\data\Json\islenmis_mevzuat_verileri.json"

with open(DOSYA, encoding="utf-8") as f:
    veri = json.load(f)

def bozuk(b):
    b = b.strip()
    return (len(b) < 15 or re.fullmatch(r"[\d\s.\-]+", b) is not None
            or b.upper().startswith(("T.C", "EK", "SAYI", "BİRİNCİ", "REHB", "DENETİM")))

def konudan_baslik(govde):
    m = re.search(r"\bKonu\s+(.+)", govde)
    if not m:
        return ""
    ham = m.group(1)
    ham = re.split(r"\s(?:GENELGE|BAKANLIK MAKAMINA|İlgi|İLGİ)\b", ham)[0]
    return " ".join(ham.split())[:150]

satirlar = []
for i, d in enumerate(veri):
    pc = d.get("page_content", "")
    m = re.search(r"MEVZUAT ADI:\s*(.+)", pc)
    t = re.search(r"MEVZUAT TÜRÜ:\s*(.+)", pc)
    baslik = m.group(1).strip() if m else ""
    tur = t.group(1).strip() if t else ""
    govde = pc.split("MEVZUAT TÜRÜ:")[-1].split("\n", 1)[-1]
    govde = " ".join(govde.split())

    if not bozuk(baslik):
        yeni, durum = baslik, "orijinal"
    else:
        yeni = konudan_baslik(govde)
        durum = "otomatik" if len(yeni) >= 10 else "elle_gerekli"
    satirlar.append([i, tur, baslik, yeni if durum != "elle_gerekli" else "", durum, govde[:250]])

with open("duzeltilmis_basliklar.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["kayit_no", "tur", "eski_baslik", "yeni_baslik", "durum", "icerik_onizleme"])
    w.writerows(satirlar)

print("Durum dağılımı:", Counter(s[4] for s in satirlar))

print("\n=== OTOMATİK DÜZELTİLENLER (kontrol et) ===")
for s in satirlar:
    if s[4] == "otomatik":
        print(f"#{s[0]} [{s[1]}] {s[2]}  ->  {s[3]}")

print("\n=== ELLE BAKILMASI GEREKENLER ===")
for s in satirlar:
    if s[4] == "elle_gerekli":
        print(f"\n#{s[0]} [{s[1]}] {s[2]}")
        print("   ", s[5])