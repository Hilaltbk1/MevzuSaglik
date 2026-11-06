"""
Basit kategori test scripti
"""

# 12 profesyonel kategori
CATEGORIES = {
    "saglik-hizmetleri-ve-kurulari": ["hastane", "kuruluş", "poliklinik", "ruhsat", "kurum tabipliği"],
    "saglik-meslekleri-ve-calisan-haklari": ["hekim", "hemşire", "tabip", "teknisyen", "personel", "çalışan", "nöbet", "mesai"],
    "hasta-haklari-ve-saglik-etigi": ["hasta hakları", "onam", "mahremiyet", "etik", "güvenlik"],
    "saglik-verileri-ve-dijital-saglik": ["veri", "dijital", "bilgi sistemi", "elektronik", "uzaktan"],
    "ilac-eczacilik-ve-tibbi-urunler": ["ilaç", "eczane", "eczacı", "reçete", "e-reçete", "kontrole tabi"],
    "tibbi-cihaz-ve-urun-guvenligi": ["tıbbi cihaz", "cihaz", "biyosidal", "sterilizasyon", "peloid"],
    "anne-cocuk-ve-ureme-sagligi": ["bebek", "çocuk", "anne", "doğum", "aile planlaması", "nüfus planlaması"],
    "halk-sagligi-ve-koruyucu-saglik": ["halk sağlığı", "aile hekimi", "tarama", "kanser", "tüberküloz", "tütün", "4207", "nargile"],
    "acil-saglik-ve-afet-yonetimi": ["acil", "ambulans", "112", "afet", "müdahale"],
    "saglik-finansmani-ve-sosyal-guvenlik": ["sgk", "sigorta", "geri ödeme", "finansman"],
    "tibbi-arastirmalar-ve-saglikta-kalite": ["araştırma", "klinik", "etik kurul", "kalite", "akreditasyon"],
    "idari-mali-ve-hukuki-islemler": ["harcama", "mali", "bakanlık", "idari", "genelge", "yönetmelik", "merkez"]
}

def classify_simple(title: str) -> list:
    title_lower = title.lower()
    categories = []
    
    for cat, keywords in CATEGORIES.items():
        if any(keyword in title_lower for keyword in keywords):
            categories.append(cat)
    
    return categories if categories else ["halk-sagligi-ve-koruyucu-saglik"]

# Test örnekleri
test_cases = [
    "AMBULANS VE ACİL BAKIM TEKNİKERLERİ TEBLİĞİ",
    "AİLE HEKİMLİĞİ KANUNU", 
    "ECZACILAR VE ECZANELER HAKKINDA",
    "4207 SAYILI KANUN UYGULAMALARI",
    "NARGİLE ŞİŞELERİNİN SAĞLIK UYARILARI",
    "BEBEK ÇOCUK ERGEN İZLEM",
    "KANSER KAYITÇILIĞI",
    "MERKEZ YÖNETİM HARCAMA BELGELERİ",
    "BİYOSİDAL ÜRÜNLER TEBLİĞİ",
    "HEMŞİRELİK KANUNU",
    "KURUM TABİPLİKLERİNİN STANDARDI",
    "HASTA HAKLARI YÖNETMELİĞİ"
]

print("🧪 12 KATEGORİLİ SINIFLANDIRMA TESTİ:")
print("=" * 70)

for title in test_cases:
    categories = classify_simple(title)
    print(f"{title[:40]:<40} → {categories}")

print(f"\n📊 Toplam kategori sayısı: {len(CATEGORIES)}")
for cat, keywords in CATEGORIES.items():
    print(f"{cat}: {keywords[:3]}...")