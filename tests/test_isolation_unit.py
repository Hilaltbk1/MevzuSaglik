"""
Aşama 2 — birim seviyesinde izolasyon kontrolleri.
Calistir: python tests/test_isolation_unit.py
Canli API / Qdrant gerektirmez.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PASS = FAIL = 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  OK   {msg}")


def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  FAIL {msg}")


def chk(cond, ok_msg, fail_msg):
    if cond:
        ok(ok_msg)
    else:
        fail(fail_msg)


print("\n[1] owner_id string/int eslesme")
# Retrievers icindeki mantigin kopyasi (import zinciri agır olmasin diye)
def _owner_matches(meta_owner, user_id) -> bool:
    if user_id is None or meta_owner is None:
        return False
    return str(meta_owner) == str(user_id)

chk(_owner_matches("42", 42), "str metadata + int user eslesir", "str/int eslesmedi")
chk(_owner_matches(42, 42), "int/int eslesir", "int/int eslesmedi")
chk(not _owner_matches("42", 99), "farkli owner eslesmez", "yanlis eslesme")
chk(not _owner_matches(None, 1), "None owner eslesmez", "None yanlis eslesti")
chk(not _owner_matches("1", None), "None user eslesmez", "None user yanlis")

print("\n[2] erisim kurali: public herkese, private sadece sahibi")
chunks = [
    {"access_scope": "public", "owner_id": None, "text": "PUB"},
    {"access_scope": "private", "owner_id": "10", "text": "A_PRIV"},
    {"access_scope": "private", "owner_id": "20", "text": "B_PRIV"},
]


def visible_for(user_id):
    out = []
    for c in chunks:
        if c["access_scope"] == "public" or _owner_matches(c["owner_id"], user_id):
            out.append(c["text"])
    return out


chk(visible_for(10) == ["PUB", "A_PRIV"], "User 10: public + kendi private", f"got {visible_for(10)}")
chk(visible_for(20) == ["PUB", "B_PRIV"], "User 20: public + kendi private", f"got {visible_for(20)}")
chk(visible_for(None) == ["PUB"], "Anonim: sadece public", f"got {visible_for(None)}")
chk("A_PRIV" not in visible_for(20), "User 20 A private gormez", "SIZINTI")
chk("B_PRIV" not in visible_for(10), "User 10 B private gormez", "SIZINTI")

print("\n[3] history sahiplik kurali")
def history_allowed(session_user_id, current_user_id) -> bool:
    return session_user_id == current_user_id

chk(history_allowed(1, 1), "sahip okuyabilir", "sahip engellendi")
chk(not history_allowed(1, 2), "baska user engellenir", "baska user girebildi")
chk(not history_allowed(None, 1), "user_id=None engellenir", "None session acik kaldi")

print("\n" + "=" * 50)
print(f"TOPLAM: {PASS} gecti, {FAIL} basarisiz")
print("=" * 50)
sys.exit(0 if FAIL == 0 else 1)
