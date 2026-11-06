"""
Mantık kontrol testi — import gerektirmez, sadece kaynak kodu okur.
Çalıştır: python tests/test_logic.py
"""
import os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()

PASS = FAIL = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")

def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")

def check(cond, ok_msg, fail_msg):
    if cond:
        ok(ok_msg)
    else:
        fail(fail_msg)

print("\n── crud.py ──────────────────────────────────────────")
crud = read("backend/database/crud.py")

check("extra_meta: dict | None = None" in crud,
      "extra_meta parametresi var",
      "extra_meta parametresi YOK")

check("file_hash = hashlib.sha256" in crud,
      "Hash duplicate kontrolü var",
      "Hash duplicate kontrolü YOK")

check('status="processing"' in crud,
      "DB kaydı processing ile başlıyor",
      "DB kaydı processing ile başlamıyor")

check("doc.metadata[\"document_id\"] = str(db_doc.id)" in crud,
      "document_id metadata'ya yazılıyor",
      "document_id metadata'ya yazılmıyor")

check("status\": \"failed\" if failed_batches" in crud or
      '"failed" if failed_batches' in crud or
      "failed" in crud,
      "Hata durumunda failed status yazılıyor",
      "Hata durumunda failed status YOK")

check("CategoryModel" in crud and "DocumentCategoryModel" in crud,
      "Kategori otomatik atama var",
      "Kategori otomatik atama YOK")

# Hash duplicate bloku for döngüsü içinde mi?
for_idx   = crud.find("for fd in file_data:")
hash_idx  = crud.find("file_hash = hashlib.sha256")
check(hash_idx > for_idx and for_idx > 0,
      "Hash kontrolü for döngüsü içinde",
      "Hash kontrolü for döngüsü DIŞINDA (kritik hata)")

print("\n── add_documents.py ─────────────────────────────────")
add = read("backend/routers/add_documents.py")

check("require_admin" in add,
      "list_existing require_admin ile korunuyor",
      "list_existing korunmuyor")

check('scope    = "private"' in add or 'scope = "private"' in add,
      "Kullanıcı yüklemesi private",
      "Kullanıcı yüklemesi private DEĞİL")

check("owner_id = None" in add,
      "Admin yüklemesinde owner_id=None",
      "Admin yüklemesinde owner_id=None YOK")

check("extra_meta" in add and "_process_upload" in add,
      "extra_meta _process_upload'a geçiliyor",
      "extra_meta geçilmiyor")

check("metadata.document_id" in add,
      "Silme document_id ile yapılıyor",
      "Silme document_id ile yapılmıyor")

check("my_documents" in add,
      "/my_documents endpoint var",
      "/my_documents endpoint YOK")

check("get_current_user" in add and "get_upload_status" in add,
      "/status endpoint auth ile korumalı",
      "/status endpoint korumasız")

# Duplicate import kontrolü
tenant_import_count = add.count("get_current_tenant")
check(tenant_import_count <= 2,
      "get_current_tenant duplicate import yok",
      f"get_current_tenant {tenant_import_count}x import edilmiş (duplicate)")

print("\n── search.py ────────────────────────────────────────")
search = read("backend/routers/search.py")

check(search.count("check_daily_quota") >= 2,
      "/ask ve /chat her ikisinde kota kontrolü var",
      "Kota kontrolü her iki endpoint'te değil")

check("current_user_id" in search,
      "current_user_id invoke'a geçiliyor",
      "current_user_id geçilmiyor")

print("\n── history.py ───────────────────────────────────────")
hist = read("backend/routers/history.py")

check("session.user_id != current_user.id" in hist,
      "User ID izolasyon kontrolü var",
      "User ID izolasyon kontrolü YOK")

print("\n── billing.py ───────────────────────────────────────")
bill = read("backend/routers/billing.py")

# checkout fonksiyonu içinde plan erken yazılıyor mu?
# "# Planı hemen DB'ye yaz" yorumu kaldı ama kod yok mu diye bak
early_write = re.search(r"def create_checkout.*?return \{", bill, re.DOTALL)
if early_write:
    checkout_body = early_write.group()
    check("tenant.plan =" not in checkout_body,
          "Checkout'ta erken plan yazımı yok",
          "Checkout'ta erken plan yazımı VAR (kritik)")
else:
    ok("Checkout fonksiyonu parse edildi")

check("checkout.session.completed" in bill,
      "Webhook handler var",
      "Webhook handler YOK")

print("\n── admin.py ─────────────────────────────────────────")
admin = read("backend/routers/admin.py")

check("ADMIN_SECRET" not in admin,
      "Eski ADMIN_SECRET temizlendi",
      "Eski ADMIN_SECRET hâlâ var")

check('"/documents"' in admin,
      "Belge listeleme endpoint var",
      "Belge listeleme endpoint YOK")

check("update_document" in admin or "PATCH" in admin or "@router.patch" in admin,
      "Belge güncelleme endpoint var",
      "Belge güncelleme endpoint YOK")

check("list_categories" in admin,
      "Kategori listeleme endpoint var",
      "Kategori listeleme endpoint YOK")

print("\n── auth.py ──────────────────────────────────────────")
auth = read("backend/dependencies/auth.py")

check("DocumentModel" not in auth,
      "auth.py'de gereksiz DocumentModel import yok",
      "auth.py'de gereksiz DocumentModel import VAR")

check("revoked=False" in auth,
      "Session revoke kontrolü var",
      "Session revoke kontrolü YOK")

print("\n── .dockerignore ────────────────────────────────────")
docker = read(".dockerignore")
for entry in ["backups/", "*.jsonl", "*.csv", "backend/data/", "*.pkl"]:
    check(entry in docker, f"'{entry}' dockerignore'da", f"'{entry}' dockerignore'da YOK")

print("\n── Hardcoded secret tarama ──────────────────────────")
SECRETS = ["60f1d8", "5ea2dd1b", "01fdd7b2"]
SCAN_FILES = [
    "backend/database/crud.py",
    "backend/routers/add_documents.py",
    "backend/routers/admin.py",
    "backend/routers/search.py",
    "backend/dependencies/auth.py",
]
for rel in SCAN_FILES:
    src = read(rel)
    found = [s for s in SECRETS if s in src]
    check(not found,
          f"{rel}: hardcoded secret yok",
          f"{rel}: hardcoded secret BULUNDU: {found}")

print("\n" + "=" * 60)
print(f"TOPLAM: {PASS} geçti, {FAIL} başarısız")
print("=" * 60)
sys.exit(1 if FAIL else 0)
