import json, csv, re
from collections import Counter

DOSYA = r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\backend\data\Json\islenmis_mevzuat_verileri.json"
CIKTI_JSON = DOSYA.replace(".json", "_duzeltilmis.json")

# kayit_no: (yeni başlık, kontrol_gerekli)
ELLE = {
    10:  ("Aile Hekimliği Tarama ve Takip Katsayısına İlişkin Yönerge ve HYP Tarama ve Takip Kılavuzu", False),
    84:  ("Okulda Diyabet / Okul Sağlığı Rehberi", True),
    104: ("Yönerge Değişikliği - Halk Sağlığı Genel Müdürlüğü", True),
    107: ("Sağlık Bakanlığına Bağlı İlçe Devlet Hastanelerinde Entegre Sağlık Hizmeti Sunulmasına İlişkin Usul ve Esaslar Hakkında Yönerge", False),
    53:  ("Aile Hekimliği Rehberi: Uygulamalar ve Mevzuat 2025", False),
    54:  ("Aile Hekimliği Uygulaması Planlama Rehberi 2021", False),
    31:  ("1 Sayılı Cumhurbaşkanlığı Teşkilatı Hakkında Cumhurbaşkanlığı Kararnamesi", False),
    61:  ("COVID-19 (SARS-CoV-2 Enfeksiyonu) Rehberi", False),
    67:  ("Doğum Sonu Bakım Yönetim Rehberi", False),
    68:  ("DSÖ Tütün Kontrolü Çerçeve Sözleşmesi Uygulama Rehberi", False),
    69:  ("Dumansız Hava Sahası Uygulama Rehberi", False),
    71:  ("Evlilik Öncesi Hemoglobinopati Tarama Programı Saha Rehberi", False),
    72:  ("Gebe Okulu Eğitim Kitabı", False),
    78:  ("Kuduz Profilaksi Rehberi", False),
    83:  ("Otizm Spektrum Bozukluğu Olan Bireylere Yönelik Sağlıklı Beslenme Önerileri Rehberi", False),
    90:  ("Zika Virüs Hastalığı Bilgilendirme ve Vaka Yönetim Rehberi", False),
    99:  ("Rahim Tahliyesi ve Sterilizasyon Hizmetlerinin Yürütülmesi ve Denetlenmesine İlişkin Tüzük", False),
    100: ("Sular Kanununun Uygulanışını Gösteren Tüzük", False),
    102: ("Uluslararası Sağlık Tüzüğü", False),
    121: ("Evlendirme Yönetmeliği", False),
    132: ("Mal Bildiriminde Bulunulması Hakkında Yönetmelik", False),
    133: ("Memurlara Yapılacak Giyecek Yardımı Yönetmeliği", False),
    84:  ("Pansiyonlu Okullar İçin Beslenme Hizmetleri Rehberi", False),
    104: ("Halk Sağlığı Genel Müdürlüğü Hizmet Birimleri ve Görevleri Hakkında Yönerge Değişikliği", False),
    106: ("Sağlık Bakanlığı 4/B Sözleşmeli Personelinin Yeniden Hizmete Alınması ve Kurum İçi Yer Değişikliğine Dair Yönerge", False),
    115: ("Danışma, Arındırma ve Rehabilitasyon Merkezleri Yönetmeliği", True),
    120: ("Erişkinler İçin Engellilik Sağlık Kurulu Raporu Yönetmeliği", True),
    122: ("Eğitim Aile Sağlığı Merkezleri Yönetmeliği: Kurumsal Sözleşme Örneği", False),
    143: ("Havza Su Kurulları ve İl Su Kurulları Yönetmeliği Ekleri", True),
}

def bozuk(b):
    b = b.strip()
    return (len(b) < 15 or re.fullmatch(r"[\d\s.\-]+", b) is not None
            or b.upper().startswith(("T.C", "EK", "SAYI", "BİRİNCİ", "REHB", "DENETİM")))

def konudan_baslik(govde):
    m = re.search(r"\bKonu\s+(.+)", govde)
    if not m:
        return ""
    ham = re.split(r"\s(?:GENELGE|BAKANLIK MAKAMINA|İlgi|İLGİ)\b", m.group(1))[0]
    return " ".join(ham.split())[:150]

with open(DOSYA, encoding="utf-8") as f:
    veri = json.load(f)

satirlar = []
for i, d in enumerate(veri):
    pc = d.get("page_content", "")
    m = re.search(r"MEVZUAT ADI:\s*(.+)", pc)
    baslik = m.group(1).strip() if m else ""
    tur = d.get("metadata", {}).get("Mevzuat_Türü", "")
    govde = " ".join(pc.split("MEVZUAT TÜRÜ:")[-1].split("\n", 1)[-1].split())

    if i in ELLE:
        yeni, kontrol = ELLE[i]; kaynak = "elle"
    elif not bozuk(baslik):
        yeni, kontrol, kaynak = baslik, False, "orijinal"
    else:
        yeni = konudan_baslik(govde); kontrol = False; kaynak = "otomatik"
        if len(yeni) < 10:
            yeni, kontrol, kaynak = baslik, True, "COZULEMEDI"

    satirlar.append([i, tur, baslik, yeni, kaynak, kontrol])
    if yeni != baslik and baslik:
        d["metadata"]["Mevzuat_Adi"] = yeni
        d["metadata"]["Mevzuat_Adi_Eski"] = baslik
        d["page_content"] = pc.replace(f"MEVZUAT ADI: {baslik}", f"MEVZUAT ADI: {yeni}", 1)

with open("basliklar_duzeltilmis.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["kayit_no", "tur", "eski_baslik", "yeni_baslik", "kaynak", "kontrol_gerekli"])
    w.writerows(satirlar)

with open(CIKTI_JSON, "w", encoding="utf-8") as f:
    json.dump(veri, f, ensure_ascii=False, indent=2)

print(Counter(s[4] for s in satirlar))
print("\nKONTROL GEREKENLER:")
for s in satirlar:
    if s[5]:
        print(f"#{s[0]} [{s[1]}] {s[3]}")
print("\nYazıldı: basliklar_duzeltilmis.csv ve", CIKTI_JSON)