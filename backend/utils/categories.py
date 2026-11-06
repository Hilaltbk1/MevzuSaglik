# backend/utils/categories.py — YENİ DOSYA

# kategori_eslesmesi.json ile uyumlu, tek resmi taksonomi
CATEGORIES = {
    "halk_sagligi":           "Halk Sağlığı ve Hastalıklar",
    "anne_cocuk_uremme":      "Anne, Çocuk ve Üreme Sağlığı",
    "beslenme_gida_su":       "Beslenme, Gıda ve Su",
    "tutun_madde":            "Tütün ve Madde Bağımlılığı",
    "acil_saglik":            "Acil Sağlık Hizmetleri",
    "hizmet_sunumu_kurumlar": "Sağlık Hizmeti Sunumu ve Kurumlar",
    "calisanlar_hasta_haklari": "Sağlık Çalışanları ve Hasta Hakları",
    "ilac_cihaz_eczacilik":   "İlaç, Eczacılık ve Tıbbi Cihaz",
    "cevre_denetim":          "Çevre Sağlığı ve Denetim",
    "genel":                  "Genel / Çapraz Konulu",
}

DESCRIPTIONS = {
    "halk_sagligi":           "Bulaşıcı ve bulaşıcı olmayan hastalıklar, salgın, aşı, tarama, kayıt sistemleri",
    "anne_cocuk_uremme":      "Gebelik, doğum, bebek-çocuk izlem, nüfus planlaması",
    "beslenme_gida_su":       "Beslenme programları, gıda ve su güvenliği",
    "tutun_madde":            "Tütün, nargile, uyuşturucu, uçucu madde ve bağımlılık merkezleri",
    "acil_saglik":            "Acil sağlık hizmetleri, ambulans, hastane öncesi hizmet",
    "hizmet_sunumu_kurumlar": "Sağlık hizmetinin örgütlenmesi, birinci basamak, kurum yapısı",
    "calisanlar_hasta_haklari": "Meslekler, atama, disiplin, etik, hasta hakları, iş sağlığı",
    "ilac_cihaz_eczacilik":   "İlaç, eczane, reçete, tıbbi cihaz",
    "cevre_denetim":          "Çevre sağlığı, kaplıca, mezarlık, tıbbi atık, denetime tabi yerler",
    "genel":                  "Emin olunmayan veya çapraz konulu belgeler",
}
# Soru sınıflandırma için anahtar kelimeler (slug -> kelimeler)
TOPIC_KEYWORDS = {
    "acil_saglik": [
        "acil", "ambulans", "112", "paramedik", "att", "acil tıp",
        "hastane öncesi", "aabt", "acil bakım", "sedye", "kurtarma",
        "müdahale", "defibrilasyon", "resüsitasyon", "triage",
    ],
    "hizmet_sunumu_kurumlar": [
        "hastane", "klinik", "aile hekimliği", "birinci basamak",
        "sağlık ocağı", "tesis", "poliklinik", "organizasyon",
        "sgk", "sosyal güvenlik", "fatura", "sevk", "muayene",
        "yataklı", "dal hastanesi", "üniversite hastanesi",
    ],
    "calisanlar_hasta_haklari": [
        "hasta hakları", "hekim", "hemşire", "personel", "nöbet",
        "meslek", "etik", "atama", "disiplin", "tabip",
        "ebe", "sağlık memuru", "malpraktis", "tıbbi hata",
        "ihraç", "görevden alma", "özlük", "maaş", "nöbet ücreti",
    ],
    "halk_sagligi": [
        "salgın", "bulaşıcı", "aşı", "aşılama", "tarama", "enfeksiyon",
        "sürveyans", "halk sağlığı", "ihbar", "bildirim",
        "karantina", "izolasyon", "pandemi", "epidemi", "vaka",
        "temas takibi", "bağışıklama",
    ],
    "anne_cocuk_uremme": [
        "gebe", "gebelik", "doğum", "bebek", "çocuk", "yenidoğan",
        "aile planlaması", "üreme", "lohusa", "anne sütü",
        "perinatal", "maternal", "çocuk sağlığı", "okul öncesi",
    ],
    "beslenme_gida_su": [
        "beslenme", "gıda", "su güvenliği", "diyet", "obezite",
        "içme suyu", "gıda güvenliği", "takviye", "vitamin",
        "mineral", "gıda katkısı", "etiket", "kalori",
    ],
    "tutun_madde": [
        "tütün", "sigara", "nargile", "bağımlılık", "uyuşturucu",
        "4207", "madde bağımlılığı", "alkol", "esrar", "eroin",
        "uçucu madde", "elektronik sigara", "satış yasağı",
    ],
    "ilac_cihaz_eczacilik": [
        "ilaç", "eczane", "reçete", "eczacı", "tıbbi cihaz",
        "farmasötik", "ruhsat", "biyoeşdeğer", "jenerik",
        "klinik araştırma", "ilaç onayı", "sağlık beyanı",
    ],
    "cevre_denetim": [
        "çevre", "tıbbi atık", "denetim", "kaplıca", "biyosidal",
        "hijyen", "mezarlık", "gürültü", "hava kirliliği",
        "pestisit", "dezenfektan", "sterilizasyon",
    ],
    "genel": [],
}

def get_all() -> dict:
    return CATEGORIES

def get_description(slug: str) -> str:
    return DESCRIPTIONS.get(slug, "")
