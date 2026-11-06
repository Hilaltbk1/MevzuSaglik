"""Türkçe metin yardımcıları: normalizasyon, tokenizer, madde/kanun no ayıklama."""
from __future__ import annotations

import os
import re
from typing import Dict, List

_TR_LOWER = str.maketrans({"İ": "i", "I": "ı"})
_FOLD = str.maketrans("ığüşöçâîû", "igusocaiu")

STEM_LEN = int(os.getenv("BM25_STEM_LEN", "5"))

_STOP = {
    "ve", "veya", "ile", "bir", "bu", "su", "o", "de", "da", "icin", "olan",
    "olarak", "gibi", "ancak", "ise", "ya", "ki", "mi", "mu", "daha", "en",
    "cok", "her", "ne", "nasil", "hangi", "midir", "mudur", "olur", "olup",
    "ilgili", "gore", "kadar", "sonra", "once", "ayni", "diger",
}
_TOKEN = re.compile(r"[a-z0-9]+")


def tr_lower(text: str) -> str:
    """Türkçe'ye uygun küçük harfe çevirme (İ→i, I→ı)."""
    return (text or "").translate(_TR_LOWER).lower()


def fold(text: str) -> str:
    """Küçük harf + Türkçe karakterleri ASCII'ye indirgeme (ı→i, ş→s ...)."""
    return tr_lower(text).translate(_FOLD)


def tokenize(text: str, stem_len: int | None = None) -> List[str]:
    """BM25 için token'lar: ASCII'ye indirgeme, stop-word atma, ön ek kökleme."""
    n = stem_len or STEM_LEN
    out: List[str] = []
    for tok in _TOKEN.findall(fold(text)):
        if tok in _STOP:
            continue
        out.append(tok if (tok.isdigit() or len(tok) <= n) else tok[:n])
    return out


# ── Madde / kanun numarası ayıklama ────────────────────────────
_ORD = r"(?:\.|'?\s*(?:inci|nci|uncu|ncu|üncü|ncü|ıncı|ncı))?"
_MADDE_A = re.compile(r"madde\s*(?:no\s*:?\s*)?(\d{1,4}(?:\s*/\s*[a-zçğıöşü])?)\b")
_MADDE_B = re.compile(r"\b(\d{1,4})\s*" + _ORD + r"\s*madde")
_KANUN = re.compile(r"\b(\d{3,5})\s*(?:sayılı|sayili|no'?lu)")


def normalize_madde_no(value: str | None) -> str | None:
    if value is None:
        return None
    v = re.sub(r"\s+", "", str(value)).upper()
    return v or None


def extract_references(question: str) -> Dict[str, List[str]]:
    """Sorudaki 'Madde 12', '12. madde', '3359 sayılı' gibi referansları döndürür."""
    q = tr_lower(question)
    maddeler: List[str] = []
    for rx in (_MADDE_A, _MADDE_B):
        for m in rx.finditer(q):
            no = normalize_madde_no(m.group(1))
            if no and no not in maddeler:
                maddeler.append(no)
    kanunlar = list(dict.fromkeys(m.group(1) for m in _KANUN.finditer(q)))
    return {"madde": maddeler, "kanun_no": kanunlar}
