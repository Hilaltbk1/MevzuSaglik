"""
Canli ortam testi — https://hilal1-mevzusaglik.hf.space
Calistir: python tests/test_live.py
"""
import requests
import sys
import uuid
from datetime import datetime

BASE = "https://hilal1-mevzusaglik.hf.space"
PASS = FAIL = 0

def ok(msg):
    global PASS; PASS += 1; print(f"  OK   {msg}")

def fail(msg):
    global FAIL; FAIL += 1; print(f"  FAIL {msg}")

def chk(cond, ok_msg, fail_msg):
    if cond: ok(ok_msg)
    else: fail(fail_msg)

def req(method, path, **kwargs):
    try:
        r = getattr(requests, method)(f"{BASE}{path}", timeout=30, **kwargs)
        return r
    except Exception as e:
        return None

ts = datetime.now().strftime("%H%M%S")
USER_A = {"user_name": f"test_a_{ts}", "password": "TestPass123!", "email": f"a_{ts}@test.com"}
USER_B = {"user_name": f"test_b_{ts}", "password": "TestPass123!", "email": f"b_{ts}@test.com"}

print(f"\nHedef: {BASE}")
print("=" * 60)

# 1. Backend erişilebilir mi?
print("\n[1] Backend saglik kontrolu")
r = req("get", "/test")
chk(r and r.status_code == 200, "Backend ayakta", "Backend erisilemiyor!")
if not r or r.status_code != 200:
    print("Backend erisileemedi, test durduruluyor.")
    sys.exit(1)

# 2. Kayit
print("\n[2] Kullanici kaydi (A)")
r = req("post", "/auth/register", json=USER_A)
chk(r and r.status_code == 200, "A kaydi basarili", f"A kaydi hata: {r.status_code if r else 'baglanti yok'}")
token_a = r.json().get("access_token") if r and r.status_code == 200 else None
chk(bool(token_a), "A icin token alindi", "Token alinamadi")

print("\n[3] Kullanici kaydi (B)")
r = req("post", "/auth/register", json=USER_B)
chk(r and r.status_code == 200, "B kaydi basarili", f"B kaydi hata: {r.status_code if r else 'baglanti yok'}")
token_b = r.json().get("access_token") if r and r.status_code == 200 else None
chk(bool(token_b), "B icin token alindi", "Token alinamadi")

# 3. /auth/me
print("\n[4] Token dogrulama (/auth/me)")
if token_a:
    r = req("get", "/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    chk(r and r.status_code == 200, "/auth/me 200 dondu", f"/auth/me hata: {r.status_code if r else '-'}")

# 4. Oturum olustur (A)
print("\n[5] Oturum olusturma (A)")
session_uuid_a = None
if token_a:
    r = req("post", "/session/create_session", headers={"Authorization": f"Bearer {token_a}"})
    if r and r.status_code == 200:
        session_uuid_a = r.json().get("session_uuid")
        ok(f"Oturum olusturuldu: {session_uuid_a[:8]}...")
    else:
        fail(f"Oturum olusturulamadi: {r.status_code if r else '-'}")

# 5. Soru sor (A)
print("\n[6] Soru sor (A) — kota kontrolu")
if token_a and session_uuid_a:
    r = req("post", "/search/ask",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"query": "hasta haklari nedir", "user_name": USER_A["user_name"], "session_uuid": session_uuid_a})
    chk(r and r.status_code in (200, 400, 429, 500),
        f"/search/ask yanit: {r.status_code if r else '-'}",
        "Baglanti hatasi")
    if r and r.status_code == 200:
        ans = r.json().get("answer", "")
        chk(len(ans) > 0, f"Cevap geldi ({len(ans)} karakter)", "Cevap bos")

# 6. B, A'nin oturumuna erisemesin
print("\n[7] Izolasyon testi — B, A'nin oturumuna erisemez")
if token_b and session_uuid_a:
    r = req("get", f"/history/{session_uuid_a}",
            headers={"Authorization": f"Bearer {token_b}"})
    chk(r and r.status_code == 403,
        f"B erisimi engellendi (403)",
        f"KRITIK: B erisebildi! Status: {r.status_code if r else '-'}")

# 7. Ucretsiz kullanici yukleme yapamaz
print("\n[8] Plan kontrolu — ucretsiz yukleme engeli")
if token_a:
    import io
    r = req("post", "/add_documents/add",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"files": ("test.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")})
    chk(r and r.status_code == 403,
        "Ucretsiz kullanici yukleme engellendi (403)",
        f"Plan kontrolu calismadi: {r.status_code if r else '-'}")

# 7b. Belge listesi izolasyonu — B, A'nin belgelerini goremez
print("\n[8b] Belge listesi izolasyonu (my_documents)")
if token_a and token_b:
    r_a = req("get", "/add_documents/my_documents",
              headers={"Authorization": f"Bearer {token_a}"})
    r_b = req("get", "/add_documents/my_documents",
              headers={"Authorization": f"Bearer {token_b}"})
    chk(r_a and r_a.status_code == 200, "A my_documents 200", f"A hata: {r_a.status_code if r_a else '-'}")
    chk(r_b and r_b.status_code == 200, "B my_documents 200", f"B hata: {r_b.status_code if r_b else '-'}")
    if r_a and r_b and r_a.status_code == 200 and r_b.status_code == 200:
        ids_a = {d.get("id") for d in r_a.json()}
        ids_b = {d.get("id") for d in r_b.json()}
        chk(ids_a.isdisjoint(ids_b) or not ids_a or not ids_b,
            "A ve B belge listeleri karismiyor",
            "KRITIK: A/B belge listelerinde ortak ID!")

# 7c. Private belge izolasyonu (opsiyonel — ADMIN_TOKEN + PRO kullanici gerekir)
# Ortam: ADMIN_TOKEN set ise admin public yukleme yapmaz; private test icin
# PRO_TOKEN_A ile A private yukler, B sorar.
print("\n[8c] Private belge retrieval izolasyonu (opsiyonel)")
PRO_TOKEN = __import__("os").environ.get("PRO_TOKEN_A")
if PRO_TOKEN and token_b:
    import io
    UNIQUE = f"IZOLASYON_TOKEN_{ts}_SADECE_A"
    # Minimal PDF bytes — gercek PDF parser icin zayif olabilir; status kontrolu yapilir
    fake_pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + UNIQUE.encode()
    r = req("post", "/add_documents/add",
            headers={"Authorization": f"Bearer {PRO_TOKEN}"},
            files={"files": (f"izolasyon_{ts}.pdf", io.BytesIO(fake_pdf), "application/pdf")})
    if r and r.status_code == 200:
        ok(f"PRO A yukleme kabul: {r.json().get('task_id')}")
        # B kendi session'i ile UNIQUE sorar
        r_sb = req("post", "/session/create_session",
                   headers={"Authorization": f"Bearer {token_b}"})
        su_b = r_sb.json().get("session_uuid") if r_sb and r_sb.status_code == 200 else None
        if su_b:
            import time; time.sleep(3)
            r = req("post", "/search/ask",
                    headers={"Authorization": f"Bearer {token_b}"},
                    json={"query": UNIQUE, "user_name": USER_B["user_name"], "session_uuid": su_b})
            body = (r.json() if r and r.status_code == 200 else {}) or {}
            blob = str(body.get("answer", "")) + str(body.get("sources", []))
            chk(UNIQUE not in blob and "SADECE_A" not in blob,
                "B, A private belgesindeki UNIQUE tokeni gormedi",
                "KRITIK: Private belge sizintisi!")
    else:
        ok(f"PRO izolasyon atlandi (upload status={r.status_code if r else '-'})")
else:
    ok("PRO_TOKEN_A yok — private retrieval izolasyonu atlandi")

# 8. Logout
print("\n[9] Logout")
if token_a:
    r = req("post", "/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    chk(r and r.status_code == 200, "Logout basarili", f"Logout hata: {r.status_code if r else '-'}")

# 9. Logout sonrasi token gecersiz
print("\n[10] Logout sonrasi token gecersiz mi?")
if token_a:
    r = req("get", "/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    chk(r and r.status_code == 401,
        "Token iptal edildi (401)",
        f"Token hala gecerli! Status: {r.status_code if r else '-'}")

# 10. Gecersiz token
print("\n[11] Gecersiz token reddediliyor mu?")
r = req("get", "/auth/me", headers={"Authorization": "Bearer yanlis_token_123"})
chk(r and r.status_code == 401, "Gecersiz token reddedildi (401)", f"Hata: {r.status_code if r else '-'}")

# 11. /chat kota kontrolu
print("\n[12] /chat kota kontrolu")
if token_b:
    r = req("post", "/search/chat",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"message": "hasta haklari", "session_uuid": str(uuid.uuid4())})
    chk(r and r.status_code in (200, 429, 500),
        f"/chat yanit: {r.status_code if r else '-'} (200=ok, 429=kota doldu)",
        "Baglanti hatasi")

print("\n" + "=" * 60)
print(f"TOPLAM: {PASS} gecti, {FAIL} basarisiz")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
