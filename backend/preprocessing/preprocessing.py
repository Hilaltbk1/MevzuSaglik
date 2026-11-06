from __future__ import annotations
import logging
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional
from backend.config.configuration import settings

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not settings.DOCUMENT_PATH:
    target_doc_path = "backend/data/Json/mevzuat_verileri.json"
else:
    target_doc_path = settings.DOCUMENT_PATH

# Vector_store.py bu değişkeni import ediyor; davranışı değiştirmedim.
file_path = os.path.join(BASE_DIR, "data", "Json", "mevzuat_verileri.json")

# ── Ayarlar ────────────────────────────────────────────────────
MERGED_MIN_LEN = 40     # birleşik hücre sayılması için en az uzunluk
MERGED_MIN_RUN = 3      # art arda en az kaç satırda aynı değer
_NULL_LIKE = {"nan", "none", "null"}

# ── Temizlik yardımcıları ──────────────────────────────────────
_INVISIBLE = dict.fromkeys(map(ord, "\u00ad\u200b\u200c\u200d\ufeff"), None)


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", s).translate(_INVISIBLE)
    return s.replace("\u00a0", " ")


def clean_cell(value: Any) -> str:
    """Tablo hücresini temizler. Hücre içi satır sonu ' | ' olur."""
    if value is None:
        return ""
    s = _normalize(str(value)).strip()
    if s.lower() in _NULL_LIKE:
        return ""
    s = re.sub(r"\s*\n\s*", " | ", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


# "MADDE 4  1 Ambulans" -> "MADDE 4- (1) Ambulans"
# Yalnızca çift boşluk VE ardından büyük harf varsa uygulanır.
_FIKRA_FIX = re.compile(
    r"^((?:MADDE|Madde)\s+\d{1,4}(?:\s*/\s*[A-Za-zÇĞİÖŞÜ])?)[ \t]{2,}(\d{1,2})[ \t]+(?=[A-ZÇĞİÖŞÜ])"
)


def clean_content_line(line: Any) -> tuple[str, bool]:
    """Madde metni satırını temizler. (satır, fıkra_düzeltildi_mi)"""
    s = _normalize(str(line)).strip()
    s, n = _FIKRA_FIX.subn(r"\1- (\2) ", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s, bool(n)


# ── Tablo ──────────────────────────────────────────────────────
def _merged_runs(rows: List[List[str]], ncols: int) -> Dict[tuple, int]:
    """Uzun ve art arda tekrar eden hücreleri bulur.

    Dönen sözlük: {(satır_idx, sütun_idx): uzunluk}  -> yalnızca koşunun İLK satırı.
    Koşunun diğer satırları (satır_idx, sütun_idx) -> 0 ile işaretlenir.
    """
    marks: Dict[tuple, int] = {}
    for c in range(ncols):
        r = 0
        while r < len(rows):
            val = rows[r][c] if c < len(rows[r]) else ""
            if len(val) < MERGED_MIN_LEN:
                r += 1
                continue
            end = r + 1
            while end < len(rows) and c < len(rows[end]) and rows[end][c] == val:
                end += 1
            if end - r >= MERGED_MIN_RUN:
                marks[(r, c)] = end - r
                for k in range(r + 1, end):
                    marks[(k, c)] = 0
            r = end
    return marks


def format_table_as_text(table_data: list, table_no: Optional[int] = None,
                          title: str = "") -> str:
    if not table_data or not isinstance(table_data, list):
        return ""

    if not isinstance(table_data[0], list):
        # Başlık satırı yok: tabloyu düz satırlar olarak koru (veri kaybı olmasın)
        flat = [clean_cell(r) for r in table_data]
        body = "\n".join(x for x in flat if x)
        head = f"TABLO {table_no} - {title}".rstrip(" -") if table_no is not None else ""
        return f"{head}\n\n{body}".strip() if body else ""

    headers = [clean_cell(h) for h in table_data[0]]
    rows = [[clean_cell(c) for c in r] for r in table_data[1:] if isinstance(r, list)]
    ncols = max([len(headers)] + [len(r) for r in rows])
    marks = _merged_runs(rows, ncols)

    out: List[str] = []
    if table_no is not None:
        out.append(f"TABLO {table_no} - {title}".rstrip(" -"))

    for idx, row in enumerate(rows, start=1):
        r0 = idx - 1
        # Birleşik hücre grubu başlıyorsa satırdan önce bir kez yaz
        for c in range(ncols):
            if marks.get((r0, c), 0) > 0:
                h = headers[c] if c < len(headers) else ""
                label = f"{h}: " if h and h.casefold() != "grup" else ""
                out.append(f"[Grup: {label}{row[c]}]")

        parts = []
        for c, value in enumerate(row):
            if not value:
                continue                      # boş değer atlanır
            if marks.get((r0, c)) is not None:
                continue                      # grup başlığına taşındı
            h = headers[c] if c < len(headers) else ""   # başlıktan fazla hücre kaybolmaz
            parts.append(f"{h}: {value}" if h else value)

        if parts:
            out.append(f"SATIR {idx}:\n" + "\n".join(parts))

    return "\n\n".join(out)


# ── Ana fonksiyon ──────────────────────────────────────────────
def flatten_mevzuat_object(mevzuat_object: Dict[str, Any], model_name=None) -> str:
    """Deterministik düzleştirme. model_name artık kullanılmaz (geri uyumluluk için duruyor)."""
    flat_parts: List[str] = []

    flat_parts.append(f"MEVZUAT ADI: {mevzuat_object.get('Mevzuat Adı', 'YOK')}")
    flat_parts.append(f"MEVZUAT TÜRÜ: {mevzuat_object.get('Mevzuat Türü', 'YOK')}")

    content_list = mevzuat_object.get("Mevzuat İçeriği", [])
    if isinstance(content_list, list) and content_list:
        lines, fixed = [], 0
        for x in content_list:
            s, was_fixed = clean_content_line(x)
            fixed += was_fixed
            if s:
                lines.append(s)
        if fixed:
            logger.info(
                "%s: %d fıkra biçimi düzeltildi",
                mevzuat_object.get("Mevzuat Adı", "?"),
                fixed,
            )
        if lines:
            flat_parts.append("\n".join(lines))

    tables = mevzuat_object.get("Tablolar", [])
    if isinstance(tables, list) and tables:
        name = str(mevzuat_object.get("Mevzuat Adı", "")).strip()
        for i, t in enumerate(tables, start=1):
            if isinstance(t, list):
                txt = format_table_as_text(t, table_no=i, title=name)
                if txt.strip():
                    flat_parts.append(txt)

    return "\n\n".join(flat_parts)


# ── Doğrulama ──────────────────────────────────────────────────
_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def _numbers(text: str) -> set[str]:
    return set(_NUM.findall(_normalize(text)))


def verify_flatten(mevzuat_object: Dict[str, Any], flat_text: str) -> Dict[str, Any]:
    """Kaynaktaki sayılar (tutar, tarih, madde no) çıktıda var mı? Eksikleri döndürür."""
    src: List[str] = [str(x) for x in (mevzuat_object.get("Mevzuat İçeriği") or [])]
    src_rows = 0
    for t in mevzuat_object.get("Tablolar") or []:
        if isinstance(t, list):
            for r in t:
                if isinstance(r, list):
                    src.extend("" if c is None else str(c) for c in r)
            src_rows += max(0, len(t) - 1)
    missing = sorted(_numbers("\n".join(src)) - _numbers(flat_text))
    out_rows = len(re.findall(r"(?m)^SATIR \d+:", flat_text))
    return {
        "missing_numbers": missing,
        "source_table_rows": src_rows,
        "output_table_rows": out_rows,
    }
