import json
from pathlib import Path

DOSYA = Path("backend/data/Json/islenmis_mevzuat_verileri.json")

with open(DOSYA, "r", encoding="utf-8") as f:
    veriler = json.load(f)

print("Veri tipi:", type(veriler).__name__)

if isinstance(veriler, list):
    print("Toplam kayıt:", len(veriler))

    for i, kayit in enumerate(veriler[:3]):
        print(f"\n--- {i + 1}. KAYIT ---")
        print("Alanlar:", list(kayit.keys()))

        for alan, deger in kayit.items():
            if isinstance(deger, dict):
                print(f"{alan} alt alanları:", list(deger.keys()))
            elif isinstance(deger, str):
                print(f"{alan}:", deger[:300])
            else:
                print(f"{alan}:", deger)

elif isinstance(veriler, dict):
    print("Anahtarlar:", list(veriler.keys()))
