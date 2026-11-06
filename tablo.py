import csv, json

esleme = json.load(open(r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\kategori_eslesmesi.json", encoding="utf-8"))
tax = esleme["taxonomy"]
satirlar = list(csv.DictReader(open(r"C:\Users\hilal\Downloads\MevzuSaglik-main\MevzuSaglik-main\duzeltilmis_basliklar.csv", encoding="utf-8-sig")))

with open("kategori_tablosu.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
# yeni
    w.writerow(["kayit_no", "tur", "baslik", "ana_kategori", "ikincil_kategori", "kontrol_gerekli"])
    for r in sorted(satirlar, key=lambda r: (tax[esleme["documents"][r["kayit_no"]]["primary"]], int(r["kayit_no"]))):
        d = esleme["documents"][r["kayit_no"]]
        ikinci = ", ".join(tax[t] for t in d["topics"][1:])
        w.writerow([r["kayit_no"], r["tur"], r["yeni_baslik"], tax[d["primary"]], ikinci,
# yeni
            "EVET" if d["needs_review"] else ""])
print("kategori_tablosu.csv oluşturuldu")