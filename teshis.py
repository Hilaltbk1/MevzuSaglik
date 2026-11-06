import json, csv, re

DOSYA = r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\backend\data\Json\islenmis_mevzuat_verileri.json"

with open(DOSYA, encoding="utf-8") as f:
    veri = json.load(f)
print("Toplam kayıt:", len(veri))
print("Anahtarlar:", list(veri[0].keys()))
if "metadata" in veri[0]:
    print("Metadata örneği:", veri[0]["metadata"])

def bozuk(b):
    b = b.strip()
    return (len(b) < 15 or re.fullmatch(r"[\d\s.\-]+", b) is not None
            or b.upper().startswith(("T.C", "EK", "SAYI", "BİRİNCİ", "REHB", "DENETİM")))

satirlar = []
for i, d in enumerate(veri):
    pc = d.get("page_content", "")
    m = re.search(r"MEVZUAT ADI:\s*(.+)", pc)
    t = re.search(r"MEVZUAT TÜRÜ:\s*(.+)", pc)
    baslik = m.group(1).strip() if m else ""
    if bozuk(baslik):
        govde = pc.split("MEVZUAT TÜRÜ:")[-1].split("\n", 1)[-1]
        onizleme = " ".join(govde.split())[:300]
        satirlar.append([i, t.group(1).strip() if t else "", baslik, onizleme])

with open("bozuk_basliklar.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["kayit_no", "tur", "baslik", "icerik_onizleme"])
    w.writerows(satirlar)

print("Bozuk başlıklı kayıt sayısı:", len(satirlar))
for s in satirlar[:8]:
    print("\n#", s[0], "|", s[1], "|", s[2])
    print("   ", s[3])