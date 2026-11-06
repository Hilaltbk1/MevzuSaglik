"""
Statik kod analizi â€” backend Ã§alÄ±ÅŸmadan import ve mantÄ±k hatalarÄ±nÄ± tespit eder.
Ã‡alÄ±ÅŸtÄ±r: python tests/test_static.py
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ERRORS   = []
WARNINGS = []

def check(cond: bool, msg: str, warn: bool = False):
    if not cond:
        (WARNINGS if warn else ERRORS).append(msg)

def parse_file(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        return ast.parse(src), src
    except SyntaxError as e:
        ERRORS.append(f"SyntaxError {path}: {e}")
        return None, ""

# â”€â”€ 1. Syntax kontrolÃ¼ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FILES = [
    "backend/database/crud.py",
    "backend/routers/add_documents.py",
    "backend/routers/admin.py",
    "backend/routers/search.py",
    "backend/routers/history.py",
    "backend/routers/billing.py",
    "backend/dependencies/auth.py",
    "backend/utils/categories.py",
]

for rel in FILES:
    path = os.path.join(ROOT, rel)
    tree, src = parse_file(path)
    if tree:
        print(f"  âœ… syntax OK: {rel}")
    else:
        print(f"  âŒ syntax FAIL: {rel}")

# â”€â”€ 2. Hardcoded secret kontrolÃ¼ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SENSITIVE = ["60f1d8", "5ea2dd1b", "01fdd7b2"]
for rel in FILES + ["frontend/app.py"]:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for s in SENSITIVE:
        if s in src:
            ERRORS.append(f"HARDCODED SECRET '{s}' found in {rel}")

# â”€â”€ 3. crud.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
crud_path = os.path.join(ROOT, "backend/database/crud.py")
_, crud_src = parse_file(crud_path)

check("extra_meta" in crud_src,
      "crud.py: extra_meta parametresi yok")
check("document_id" in crud_src and "db_doc.id" in crud_src,
      "crud.py: document_id chunk metadata'sÄ±na yazÄ±lmÄ±yor")
check("hashlib.sha256" in crud_src,
      "crud.py: hash duplicate kontrolÃ¼ yok")
check('status="processing"' in crud_src,
      "crud.py: DB kaydÄ± processing status ile baÅŸlamÄ±yor")
check("content_hash=file_hash" in crud_src,
      "crud.py: content_hash DB'ye yazÄ±lmÄ±yor")

# â”€â”€ 4. add_documents.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
add_path = os.path.join(ROOT, "backend/routers/add_documents.py")
_, add_src = parse_file(add_path)

check("require_admin" in add_src,
      "add_documents.py: list_existing require_admin ile korunmuyor")
check("UserRole.admin" in add_src,
      "add_documents.py: role bazlÄ± scope belirlenmesi yok")
check('scope    = "private"' in add_src or 'scope = "private"' in add_src,
      "add_documents.py: kullanÄ±cÄ± yÃ¼klemesi private deÄŸil")
check("extra_meta" in add_src,
      "add_documents.py: extra_meta _process_upload'a geÃ§ilmiyor")
check("metadata.document_id" in add_src,
      "add_documents.py: silme document_id ile yapÄ±lmÄ±yor")
check("my_documents" in add_src,
      "add_documents.py: /my_documents endpoint yok")

# â”€â”€ 5. search.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
search_path = os.path.join(ROOT, "backend/routers/search.py")
_, search_src = parse_file(search_path)

check("check_daily_quota" in search_src,
      "search.py: /chat endpoint kota kontrolÃ¼ yok")
check("current_user_id" in search_src,
      "search.py: current_user_id invoke'a geÃ§ilmiyor")

# â”€â”€ 6. history.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
hist_path = os.path.join(ROOT, "backend/routers/history.py")
_, hist_src = parse_file(hist_path)

check("session.user_id" in hist_src,
      "history.py: user_id izolasyon kontrolÃ¼ yok")

# â”€â”€ 7. billing.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
bill_path = os.path.join(ROOT, "backend/routers/billing.py")
_, bill_src = parse_file(bill_path)

# PlanÄ± hemen yazÄ±yor mu? (webhook olmadan)
lines = bill_src.split("\n")
checkout_func_lines = []
in_checkout = False
for line in lines:
    if "def create_checkout" in line:
        in_checkout = True
    if in_checkout:
        checkout_func_lines.append(line)
    if in_checkout and line.strip().startswith("return "):
        break

checkout_body = "\n".join(checkout_func_lines)
check(
    "tenant.plan = " not in checkout_body,
    "billing.py: checkout'ta plan erken yazÄ±lÄ±yor (webhook olmadan)"
)

# â”€â”€ 8. admin.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
admin_path = os.path.join(ROOT, "backend/routers/admin.py")
_, admin_src = parse_file(admin_path)

check("GET /admin/documents" in admin_src or '"/documents"' in admin_src or "@router.get" in admin_src,
      "admin.py: belge listeleme endpoint yok")
check("require_admin" in admin_src,
      "admin.py: require_admin kullanÄ±lmÄ±yor")
check("ADMIN_SECRET" not in admin_src,
      "admin.py: eski ADMIN_SECRET hÃ¢lÃ¢ var")

# â”€â”€ 9. auth.py Ã¶zel kontroller â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
auth_path = os.path.join(ROOT, "backend/dependencies/auth.py")
_, auth_src = parse_file(auth_path)

check("DocumentModel" not in auth_src,
      "auth.py: gereksiz DocumentModel import var (circular import riski)")

# â”€â”€ 10. .dockerignore kontrolÃ¼ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
docker_path = os.path.join(ROOT, ".dockerignore")
with open(docker_path, encoding="utf-8") as f:
    docker_src = f.read()

for entry in ["backups/", "*.jsonl", "*.csv", "backend/data/", "*.pkl"]:
    check(entry in docker_src, f".dockerignore: '{entry}' eksik", warn=True)

# â”€â”€ SONUÃ‡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "=" * 60)
if ERRORS:
    print(f"âŒ {len(ERRORS)} HATA:")
    for e in ERRORS:
        print(f"   â€¢ {e}")
else:
    print("âœ… Hata yok")

if WARNINGS:
    print(f"\nâš ï¸  {len(WARNINGS)} UYARI:")
    for w in WARNINGS:
        print(f"   â€¢ {w}")

print("=" * 60)
sys.exit(1 if ERRORS else 0)

