import json

DOSYA = r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\backend\data\Json\islenmis_mevzuat_verileri.json"
KAYITLAR = [31, 53, 84, 104, 106, 115, 120, 122, 143]

with open(DOSYA, encoding="utf-8") as f:
    veri = json.load(f)

for i in KAYITLAR:
    pc = veri[i]["page_content"]
    govde = " ".join(pc.split("MEVZUAT TÜRÜ:")[-1].split())
    print(f"\n{'='*60}\n#{i}  (uzunluk: {len(govde)} karakter)\n{govde[:700]}")