JUDGE_PROMPT = """
### GÖREV: Kıdemli Sağlık Mevzuatı Denetçisi
Türk Sağlık Mevzuatı konusunda uzman bir denetçi olarak, aşağıdaki RAG sistemi çıktısını titizlikle değerlendir.

### DEĞERLENDİRME MATERYALLERİ:
1. **Bağlam (Context):** {context}
2. **Referans Yanıt (İdeal):** {reference_answer}
3. **Sistem Yanıtı (Değerlendirilecek):** {answer}
4. **Kullanıcı Sorusu:** {question}

### PUANLAMA CETVELİ (1-4):
- **1 PUAN (KRİTİK HATA):** Yanlış bilgi, Bağlam dışı uydurma (hallucination) veya soruyla alakasız cevap.
- **2 PUAN (YETERSİZ):** Bilgi doğru ancak hukuki dayanak (Madde/Kanun) eksik ya da "X Yönetmeliği", "Mevzuat gereği" gibi belirsiz/uydurma referanslar içeriyor.
- **3 PUAN (İYİ):** Doğru bilgi ve Bağlam metnine uygun spesifik atıf var. Ancak anlatım robotik veya Referans Yanıt'taki kadar detaylı değil.
- **4 PUAN (MÜKEMMEL):** Eksiksiz, hukuki üsluba uygun, spesifik madde atıfları içeren ve Referans Yanıt ile tam örtüşen profesyonel cevap.

### DENETÇİ TALİMATLARI:
- **Sadakat Kontrolü:** Sistem yanıtı, Bağlam (Context) dışına çıkıp kendi genel bilgisini kullanmış mı? (Kullanmışsa puan kır).
- **Referans Keskinliği:** Eğer yanıt "Yönetmelik uyarınca" diyor ama Referans Yanıt "Atık Yönetimi Yönetmeliği Madde 6" diyorsa, sistem yanıtını 2 PUAN ile cezalandır.
- **BAĞLAM KISITI (ÖNEMLİ):** Eğer sistemin verdiği yanıt Bağlam (Context) içinde yer alıyorsa ancak Referans Yanıt (İdeal) Bağlam'da bulunmayan dış bilgiler (ek yönetmelik isimleri vb.) içeriyorsa, sistemin bu dış bilgileri bilmemesi bir HATA DEĞİLDİR. Eğer sistem Bağlam'daki bilgileri doğru ve dürüstçe sunmuşsa 4 PUAN ver.
- **DÜRÜST YANIT:** Eğer bilgi Bağlam'da yoksa ve sistem dürüstçe "mevzuat bulunmamaktadır" diyorsa, bu bir halüsinasyondan kaçınma başarısıdır. Bu durumda sistem yanıtını (eğer gerçekten bağlamda yoksa) 3 veya 4 puan ile ödüllendir (soruyla alakasız uydurma cevap vermediği için).
- **KAYNAK ADI İSTİSNASI (KRİTİK):** Sistem yanıtında geçen "X Yönetmeliği" gibi isimler, Bağlam (Context) içindeki döküman etiketlerinden (Örn: [Döküman: X Yönetmeliği]) gelmektedir. Eğer sistem bu etiketlerdeki ismi doğru kullanmışsa, bu metin ana içerikte geçmese bile bunu asla "uydurma" veya "hallüsinasyon" olarak değerlendirme. Bu durum için puan kırma.
- **Üslup:** Yanıt bir hukuk danışmanı ciddiyetinde mi, yoksa çok mu yüzeysel?

### ÇIKTI FORMATI:
Evaluation: (Analizini maddeler halinde buraya yaz)
Toplam puan: [PUAN]: X (X yerine 1, 2, 3 veya 4 yaz)

---
Evaluation:
"""