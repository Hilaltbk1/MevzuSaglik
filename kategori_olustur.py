import json
from collections import Counter

TAX = {
 "halk_sagligi": "Halk Sağlığı ve Hastalıklar",
 "anne_cocuk_uremme": "Anne, Çocuk ve Üreme Sağlığı",
 "beslenme_gida_su": "Beslenme, Gıda ve Su",
 "tutun_madde": "Tütün ve Madde Bağımlılığı",
 "acil_saglik": "Acil Sağlık Hizmetleri",
 "hizmet_sunumu_kurumlar": "Sağlık Hizmeti Sunumu ve Kurumlar",
 "calisanlar_hasta_haklari": "Sağlık Çalışanları ve Hasta Hakları",
 "ilac_cihaz_eczacilik": "İlaç, Eczacılık ve Tıbbi Cihaz",
 "cevre_denetim": "Çevre Sağlığı ve Denetim",
 "genel": "Genel / Çapraz Konulu",
}
H,A,B,T,AC,HS,C,I,CE,G = ("halk_sagligi","anne_cocuk_uremme","beslenme_gida_su","tutun_madde","acil_saglik",
 "hizmet_sunumu_kurumlar","calisanlar_hasta_haklari","ilac_cihaz_eczacilik","cevre_denetim","genel")

# kayit_no: (ana, ikincil veya None, kontrol_gerekli)
M = {
0:(T,CE,0),1:(CE,None,0),2:(AC,C,0),3:(HS,None,0),4:(G,None,0),5:(T,None,0),6:(T,None,0),7:(T,CE,0),8:(CE,None,1),9:(G,None,1),
10:(HS,None,0),11:(HS,C,0),12:(A,None,0),13:(HS,None,0),14:(I,HS,0),15:(I,None,0),16:(C,HS,0),17:(A,H,0),18:(H,None,0),19:(I,T,0),
20:(HS,None,0),21:(HS,None,0),22:(I,None,0),23:(H,None,0),24:(H,None,0),25:(HS,None,0),26:(C,None,0),27:(B,A,0),
28:(T,None,0),29:(HS,None,0),30:(G,None,0),31:(G,None,1),32:(C,None,0),33:(I,None,0),34:(C,None,0),35:(C,None,0),36:(C,None,1),
37:(G,None,1),38:(A,None,0),39:(HS,None,1),40:(HS,None,0),41:(B,None,1),42:(C,None,0),43:(C,None,0),44:(T,None,0),45:(H,CE,0),
46:(T,None,0),47:(T,None,0),48:(T,None,0),49:(B,None,0),50:(A,None,0),51:(C,None,0),
52:(A,AC,0),53:(HS,None,0),54:(HS,None,0),55:(A,None,0),56:(A,None,0),57:(H,None,0),58:(B,A,0),59:(A,None,0),60:(H,None,0),61:(H,None,0),
62:(A,B,0),63:(B,A,0),64:(CE,None,0),65:(CE,None,1),66:(B,None,0),67:(A,None,0),68:(T,None,0),69:(T,None,0),70:(H,None,0),71:(H,A,0),
72:(A,None,0),73:(H,None,0),74:(H,None,1),75:(AC,H,0),76:(H,None,0),77:(G,None,1),78:(H,None,0),79:(H,None,0),80:(H,CE,0),81:(H,None,0),
82:(H,None,0),83:(B,None,0),84:(B,None,0),85:(B,None,0),86:(H,None,0),87:(B,None,0),88:(B,None,0),89:(H,HS,0),90:(H,None,0),
91:(B,None,0),92:(B,HS,0),93:(HS,None,0),94:(HS,None,0),
95:(CE,None,0),96:(H,A,0),97:(H,CE,1),98:(B,CE,0),99:(A,None,0),100:(B,CE,0),101:(C,None,0),102:(H,None,0),
103:(G,None,1),104:(HS,None,0),105:(HS,None,0),106:(C,None,0),107:(HS,None,0),108:(HS,None,0),109:(HS,None,0),110:(CE,None,0),
111:(AC,None,0),112:(AC,None,0),113:(HS,None,0),114:(HS,None,0),115:(T,HS,1),116:(H,None,0),117:(CE,None,0),118:(B,None,0),119:(H,CE,0),
120:(HS,None,1),121:(G,None,1),122:(HS,None,0),123:(H,HS,0),124:(H,None,0),125:(C,None,0),126:(C,None,0),127:(H,A,0),128:(C,None,0),
129:(H,None,0),130:(H,None,0),131:(CE,None,0),132:(C,None,1),133:(C,None,0),134:(CE,None,0),135:(G,None,0),136:(A,C,0),137:(C,None,0),
138:(C,None,0),139:(HS,None,0),140:(HS,None,0),141:(C,None,0),142:(C,None,0),143:(CE,B,1),144:(CE,None,0),145:(I,None,0),146:(HS,None,0),
147:(CE,None,0),148:(CE,None,0),149:(C,None,0),150:(G,None,1),151:(B,CE,0),
}
assert sorted(M) == list(range(152))
out = {"taxonomy_version": "v1", "taxonomy": TAX, "documents": {
 str(k): {"topics": [v[0]] + ([v[1]] if v[1] else []), "primary": v[0],
          "needs_review": bool(v[2]), "classified_by": "claude_draft"} for k, v in M.items()}}
json.dump(out, open("kategori_eslemesi.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("kategori_eslemesi.json oluşturuldu")
for k, n in Counter(v[0] for v in M.values()).most_common():
    print(n, k)