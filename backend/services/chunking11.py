"""
Yapıya duyarlı, belge türünden bağımsız parent-child chunk'lama.

Katmanlar
  1. Ortak katman   : metin temizleme, boş kontrol, güvenli yedek bölme (_pack)
  2. Yapı tanıma    : madde / geçici madde / ek / fıkra / başlık hiyerarşisi tespiti
  3. Strateji seçimi: tespit edilen yapıya göre  madde | baslikli | duz
                      (Mevzuat_Türü etiketi yalnızca ipucudur, karar vermez)
  4. Doğrulama      : şüpheli bölünen belgeler `review_flags` ile işaretlenir
  5. RAG katmanı    : child araması + parent bağlamı + kaynak etiketi (retrieval tarafı)

belge → bölüm/başlık → madde|bölüm → (parent bloğu) → child chunk

- Arama child chunk üzerinde yapılır, LLM'e parent (madde) bağlamı verilir.
- Her chunk'a madde no, madde başlığı, bölüm, parent_id, child_index yazılır.
- Embedding/BM25 metnine deterministik başlık eklenir (contextual_text);
  saklanan page_content ise temiz gövde metnidir.
- Child'lar örtüşmesizdir; parent = child'ların "\n" ile birleşimidir.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.services.text_utils import normalize_madde_no

PARENT_MAX = 4000
CHILD_MAX = 900
CHILD_MIN = 200

_MADDE_RE = re.compile(
    r"^\s*(?:(?P<pre>Geçici|GEÇİCİ|Ek|EK)\s+)?(?:Madde|MADDE)\s+"
    r"(?P<no>\d{1,4}(?:\s*/\s*[A-Za-zÇĞİÖŞÜ])?)(?=\s|[-–—.:(]|$)"
)
_BOLUM_RE = re.compile(r"(?:[A-ZÇĞİÖŞÜ0-9\.]+\s+){0,2}(?:BÖLÜM|KISIM)")
_HEADER_LINE = re.compile(r"^\s*MEVZUAT (?:ADI|TÜRÜ)\s*:", re.I)
_EK_RE = re.compile(r"^\s*(?:EK|Ek)\s*[-–]?\s*(?P<no>\d{1,3}|[A-ZÇĞİÖŞÜ])(?=\s|[-–:.]|$)")
_FIKRA_RE = re.compile(r"^\s*\((\d{1,3})\)\s")
# "1. Giriş", "2.3.1 Tanım", "3) Yöntem" gibi numaralı başlıklar
_NUM_HEAD_RE = re.compile(r"^\s*(?P<num>\d{1,2}(?:\.\d{1,2}){0,3})[.)]?\s+(?P<t>[A-ZÇĞİÖŞÜ][^\n]{2,90})$")


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def doc_key_for(title: str, salt: str = "") -> str:
    return hashlib.sha1(f"{salt}|{title}".encode("utf-8")).hexdigest()[:12]


# ── Başlık / bağlam metni ──────────────────────────────────────
def madde_label(meta: Dict[str, Any]) -> str:
    if meta.get("kind") == "ek" and meta.get("ek_no"):
        return f"Ek-{meta['ek_no']}"
    no = meta.get("madde_no")
    if not no:
        return meta.get("section_title") or ""
    prefix = {"G": "Geçici Madde ", "E": "Ek Madde "}.get(str(meta.get("madde_tur") or "")[:1], "Madde ")
    label = f"{prefix}{no}"
    if meta.get("madde_title"):
        label += f" ({meta['madde_title']})"
    return label


def source_label(meta: Dict[str, Any]) -> str:
    name = meta.get("Mevzuat_Adi") or "Bilinmeyen"
    ml = madde_label(meta)
    return f"{name}, {ml}" if ml else name


def contextual_text(meta: Dict[str, Any], body: str) -> str:
    """Embedding ve BM25 için: 'Mevzuat Adı > Bölüm > Madde 5 (Başlık)' + gövde."""
    parts = [meta.get("Mevzuat_Adi") or ""]
    if meta.get("bolum"):
        parts.append(meta["bolum"])
    ml = madde_label(meta)
    if ml:
        parts.append(ml)
    header = " > ".join(p for p in parts if p)
    return f"[{header}]\n{body}" if header else body


# ── Yardımcılar ────────────────────────────────────────────────
def _hard_split(line: str, limit: int) -> List[str]:
    if len(line) <= limit:
        return [line]
    pieces, cur = [], ""
    for sent in re.split(r"(?<=[.;:])\s+", line):
        if len(sent) > limit:
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.extend(sent[i:i + limit] for i in range(0, len(sent), limit))
            continue
        if cur and len(cur) + 1 + len(sent) > limit:
            pieces.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        pieces.append(cur)
    return pieces


def _pack(text: str, limit: int) -> List[str]:
    """Satır sınırlarını koruyarak metni <= limit karakterlik bloklara paketler."""
    lines: List[str] = []
    for ln in text.split("\n"):
        lines.extend(_hard_split(ln, limit))
    blocks, cur = [], ""
    for ln in lines:
        if cur and len(cur) + 1 + len(ln) > limit:
            blocks.append(cur)
            cur = ln
        else:
            cur = f"{cur}\n{ln}" if cur else ln
    if cur:
        blocks.append(cur)
    return blocks


def _merge_small(blocks: List[str], limit: int) -> List[str]:
    out: List[str] = []
    for b in blocks:
        if out and len(b) < CHILD_MIN and len(out[-1]) + 1 + len(b) <= int(limit * 1.3):
            out[-1] = f"{out[-1]}\n{b}"
        else:
            out.append(b)
    return out


def _is_title_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 100 or len(s.split()) > 12:
        return False
    if s[-1] in ".,;:":
        return False
    if _MADDE_RE.match(s) or _BOLUM_RE.fullmatch(s):
        return False
    return s[0].isupper()


# ── Ayrıştırma ─────────────────────────────────────────────────
def parse_units(text: str) -> List[Dict[str, Any]]:
    """Metni madde birimlerine ayırır. Madde işareti yoksa tek 'blok' birimi döner."""
    lines = [ln.rstrip() for ln in text.replace("\r", "").split("\n")]
    while lines and (not lines[0].strip() or _HEADER_LINE.match(lines[0])):
        lines.pop(0)

    units: List[Dict[str, Any]] = [
        {"madde_no": None, "madde_tur": None, "title": None, "bolum": None, "lines": []}
    ]
    bolum: Optional[str] = None
    last_no: Optional[int] = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if s and _BOLUM_RE.fullmatch(s):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            bolum = f"{s} - {nxt}" if nxt and len(nxt) < 150 and not _MADDE_RE.match(nxt) else s
            units[-1]["lines"].append(ln)
            i += 1
            continue

        m = _MADDE_RE.match(ln)
        accept = False
        if m:
            pre = m.group("pre")
            no_txt = normalize_madde_no(m.group("no"))
            num = int(re.match(r"\d+", no_txt).group(0))
            if pre:
                accept = True
            elif last_no is None:
                accept = num <= 50
            else:
                accept = last_no < num <= last_no + 40 or num == last_no
        if accept:
            tur = (m.group("pre") or "")[:1].upper() or None
            title = None
            prev_lines = units[-1]["lines"]
            while prev_lines and not prev_lines[-1].strip():
                prev_lines.pop()
            if prev_lines and _is_title_line(prev_lines[-1]):
                title = prev_lines.pop().strip()
            if not m.group("pre"):
                last_no = num
            units.append({"madde_no": no_txt, "madde_tur": tur, "title": title,
                          "bolum": bolum, "lines": [ln]})
        else:
            units[-1]["lines"].append(ln)
        i += 1

    for u in units:
        if u["madde_no"] is None:
            u["bolum"] = u["bolum"] or None
    return units


# ── Yapı tespiti ───────────────────────────────────────────────
def _is_upper_heading(s: str) -> bool:
    s = s.strip()
    letters = [c for c in s if c.isalpha()]

    if len(s) < 4 or len(s) > 90 or len(letters) < 4:
        return False

    if s[-1] in ".,;:":
        return False

    normalized = re.sub(
        r"[^A-ZÇĞİÖŞÜ0-9 ]+",
        "",
        " ".join(s.upper().split())
    )

    # Broşür tasarımı ve sayfa düzeninden gelen ifadeler.
    decorative_labels = {
        "TEDBİR",
        "KONTROL",
        "MÜDAHALE",
        "SAĞLIK KURULUŞU",
        "HAVANI KORU",
        "KENEYİ HAFİFE ALMAYIN",
        "TEDBİRİ ELDEN BIRAKMAYIN",
    }

    if normalized in decorative_labels:
        return False

    # Tablo alanları bölüm başlığı olarak değerlendirilmemeli.
    table_labels = {
        "HAVZA ADI",
        "KOORDİNATÖR VALİLİK",
        "HAVZADA BULUNAN DİĞER İLLER",
        "NO",
    }

    if (
            normalized in table_labels
            or normalized.startswith("HAVZA ADI ")
            or normalized.startswith("KOORDİNATÖR VALİLİK ")
            or normalized.startswith("HAVZADA BULUNAN DİĞER İLLER ")
    ):
        return False

    return (
        sum(c.isupper() for c in letters) / len(letters) >= 0.8
        and not _MADDE_RE.match(s)
    )
def detect_structure(text: str, type_hint: str | None = None) -> Dict[str, Any]:
    """Metnin yapısını ölçer; strateji ('madde' | 'baslikli' | 'duz') seçer."""
    units = parse_units(text)
    madde_units = [u for u in units if u["madde_no"] and not u["madde_tur"]]
    nums = []
    for u in madde_units:
        m = re.match(r"\d+", u["madde_no"])
        if m:
            nums.append(int(m.group(0)))
    gaps = sum(1 for a, b in zip(nums, nums[1:]) if b - a > 3)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    heads = [ln for ln in lines if _NUM_HEAD_RE.match(ln) or _is_upper_heading(ln)]
    hint = (type_hint or "").lower()

    if len(nums) >= 3 and gaps <= max(2, len(nums) // 5):
        kind = "madde"
    elif len(heads) >= 3 or ("rehber" in hint and len(heads) >= 2):
        kind = "baslikli"
    else:
        kind = "duz"
    return {"kind": kind, "madde_count": len(nums), "madde_gaps": gaps,
            "heading_count": len(heads), "length": len(text)}


def parse_heading_units(text: str) -> List[Dict[str, Any]]:
    """Madde işareti olmayan belgeler (rehber, genelge, protokol) için başlık hiyerarşisi."""
    lines = [ln.rstrip() for ln in text.replace("\r", "").split("\n")]
    while lines and (not lines[0].strip() or _HEADER_LINE.match(lines[0])):
        lines.pop(0)
    units = [{"madde_no": None, "madde_tur": None, "title": None, "bolum": None,
              "section_title": None, "lines": []}]
    stack: List[tuple[int, str]] = []          # (derinlik, başlık)
    for ln in lines:
        s = ln.strip()
        m = _NUM_HEAD_RE.match(s) if s else None
        depth = None
        title = None
        if m:
            depth = m.group("num").count(".") + 1
            title = f"{m.group('num')} {m.group('t').strip()}"
        elif s and _is_upper_heading(s):
            depth, title = 1, s
        if title and len(s) <= 90:
            while stack and stack[-1][0] >= depth:
                stack.pop()
            stack.append((depth, title))
            path = " > ".join(t for _, t in stack)
            units.append({"madde_no": None, "madde_tur": None, "title": None,
                          "bolum": path, "section_title": title, "lines": [ln]})
        else:
            units[-1]["lines"].append(ln)
    return _merge_tiny_units(units)


def _merge_tiny_units(units: List[Dict[str, Any]], min_chars: int = 200) -> List[Dict[str, Any]]:
    """Gövdesi çok kısa bölümleri (tek satırlık başlıklar) sonraki bölümün başına katar."""
    out: List[Dict[str, Any]] = []
    carry: List[str] = []
    for idx, u in enumerate(units):
        lines = carry + u["lines"]
        carry = []
        size = len("\n".join(lines).strip())
        if size < min_chars and idx < len(units) - 1:
            carry = lines
            continue
        out.append(dict(u, lines=lines))
    if carry:
        if out:
            out[-1]["lines"] = out[-1]["lines"] + carry
        else:
            out.append(dict(units[-1], lines=carry))
    return out


def _split_fikra(text: str, limit: int) -> List[tuple[str, str | None]]:
    """(1) (2) fıkra işaretleri varsa fıkra sınırında paketler. [(metin, 'fıkra aralığı')]"""
    segs: List[tuple[str, str]] = []
    cur: List[str] = []
    cur_no = None
    for ln in text.split("\n"):
        m = _FIKRA_RE.match(ln)
        if m and cur:
            segs.append(("\n".join(cur), cur_no))
            cur, cur_no = [ln], m.group(1)
        else:
            if m:
                cur_no = m.group(1)
            cur.append(ln)
    if cur:
        segs.append(("\n".join(cur), cur_no))
    if len([s for s in segs if s[1]]) < 2:
        return [(b, None) for b in _pack(text, limit)]
    out: List[tuple[str, str | None]] = []
    buf, nos = "", []
    for seg, no in segs:
        for piece in _pack(seg, limit):
            if buf and len(buf) + 1 + len(piece) > limit:
                out.append((buf, f"{nos[0]}-{nos[-1]}" if len(nos) > 1 and nos[0] != nos[-1] else (nos[0] if nos else None)))
                buf, nos = piece, [no] if no else []
            else:
                buf = f"{buf}\n{piece}" if buf else piece
                if no and no not in nos:
                    nos.append(no)
    if buf:
        out.append((buf, f"{nos[0]}-{nos[-1]}" if len(nos) > 1 and nos[0] != nos[-1] else (nos[0] if nos else None)))
    return out


def build_chunks(
    doc_text: str,
    base_meta: Dict[str, Any],
    *,
    doc_key: str,
    parent_max: int = PARENT_MAX,
    child_max: int = CHILD_MAX,
    type_hint: str | None = None,
) -> List[Chunk]:
    """Belgeyi tespit edilen yapıya göre parent-child chunk'lara böler."""
    text = (doc_text or "").replace("\x00", " ").strip()
    if not text:
        return []
    profile = detect_structure(text, type_hint or base_meta.get("Mevzuat_Türü"))
    kind_doc = profile["kind"]
    if kind_doc == "madde":
        units = _split_eks(parse_units(text))
    elif kind_doc == "baslikli":
        units = parse_heading_units(text)
    else:
        units = [{"madde_no": None, "madde_tur": None, "title": None, "bolum": None,
                  "section_title": None, "lines": text.split("\n")}]
    has_madde = kind_doc == "madde"

    chunks: List[Chunk] = []
    for u_idx, u in enumerate(units):
        body = "\n".join(u["lines"]).strip()
        if not body:
            continue
        if u.get("ek_no"):
            unit_id, kind = f"EK{u['ek_no']}", "ek"
        elif u["madde_no"]:
            unit_id, kind = f"{(u['madde_tur'] or 'M')}{u['madde_no']}", "madde"
        elif u_idx == 0 and kind_doc != "duz":
            unit_id, kind = "giris", "giris"
        else:
            unit_id, kind = f"blok{u_idx}", "blok"

        parents = _pack(body, parent_max) if len(body) > parent_max else [body]
        for p_idx, parent_text in enumerate(parents):
            parent_id = f"{doc_key}:{unit_id}:u{u_idx}:{p_idx}"
            if kind == "madde":
                pieces = _split_fikra(parent_text, child_max)
            else:
                pieces = [(b, None) for b in _pack(parent_text, child_max)]
            merged: List[tuple[str, str | None]] = []
            for b, f in pieces:
                if merged and len(b) < CHILD_MIN and len(merged[-1][0]) + 1 + len(b) <= int(child_max * 1.3):
                    merged[-1] = (f"{merged[-1][0]}\n{b}", merged[-1][1])
                else:
                    merged.append((b, f))
            for c_idx, (kid, fikra) in enumerate(merged):
                meta = dict(base_meta)
                meta.update({
                    "doc_key": doc_key,
                    "parent_id": parent_id,
                    "child_index": c_idx,
                    "child_count": len(merged),
                    "chunk_id": f"{parent_id}:{c_idx}",
                    "kind": kind,
                    "structure": kind_doc,
                })
                if u["madde_no"]:
                    meta["madde_no"] = u["madde_no"]
                    if u["madde_tur"]:
                        meta["madde_tur"] = u["madde_tur"]
                if u.get("ek_no"):
                    meta["ek_no"] = u["ek_no"]
                if u["title"]:
                    meta["madde_title"] = u["title"]
                if u.get("section_title"):
                    meta["section_title"] = u["section_title"]
                if u["bolum"]:
                    meta["bolum"] = u["bolum"]
                if fikra:
                    meta["fikra"] = fikra
                chunks.append(Chunk(text=kid, metadata=meta))

    flags = validate_chunks(text, chunks, profile)
    for c in chunks:
        c.metadata["needs_review"] = bool(flags)
    if chunks:
        chunks[0].metadata["review_flags"] = flags
    return chunks


def _split_eks(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Madde birimlerinin içinde 'EK-1', 'Ek 2' satırı görülürse yeni ek birimi açar."""
    out: List[Dict[str, Any]] = []
    for u in units:
        cur = dict(u, lines=[])
        for ln in u["lines"]:
            s = ln.strip()
            m = _EK_RE.match(ln)
            if m and len(s) <= 80 and not s.endswith(".") and (s.isupper() or len(s.split()) <= 4):
                if cur["lines"]:
                    out.append(cur)
                cur = {"madde_no": None, "madde_tur": None, "title": s, "bolum": u.get("bolum"),
                       "section_title": None, "ek_no": m.group("no"), "lines": [ln]}
            else:
                cur["lines"].append(ln)
        out.append(cur)
    return out


# ── Doğrulama katmanı ──────────────────────────────────────────
def validate_chunks(text: str, chunks: List[Chunk], profile: Dict[str, Any]) -> List[str]:
    """Şüpheli bölünmeleri işaretler (boş liste = sorun yok)."""
    flags: List[str] = []
    if not chunks:
        return ["bos_cikti"]
    n = len(chunks)
    covered = sum(len(c.text) for c in chunks)
    if covered < 0.85 * len(text.strip()):
        flags.append("kapsam_dusuk")
    small = sum(1 for c in chunks if len(c.text) < 80)
    if n >= 8 and small / n > 0.30:
        flags.append("cok_kucuk_chunk")
    if profile["kind"] == "madde" and profile["madde_gaps"] > 2:
        flags.append("madde_numarasi_atlamasi")
    if profile["kind"] == "duz" and profile["length"] > 20000:
        flags.append("uzun_belgede_yapi_bulunamadi")
    if profile["kind"] == "baslikli" and profile["heading_count"] > profile["length"] / 250:
        flags.append("asiri_baslik_algisi")
    parents: Dict[str, int] = {}
    for c in chunks:
        parents[c.metadata["parent_id"]] = parents.get(c.metadata["parent_id"], 0) + 1
    if parents and max(parents.values()) > 12:
        flags.append("cok_uzun_birim")
    if profile["kind"] == "madde":
        first = next((c for c in chunks if c.metadata.get("kind") == "giris"), None)
        if first and len(first.text) > 6000:
            flags.append("uzun_giris_blogu")
    return flags


def assemble_parent(children: List[Dict[str, Any]], matched_idx: set[int], cap: int) -> str:
    """children: [{'child_index', 'text'}] (sıralı). Cap'i aşarsa eşleşen child çevresine pencere açar."""
    children = sorted(children, key=lambda c: c["child_index"])
    total = sum(len(c["text"]) + 1 for c in children)
    if total <= cap:
        return "\n".join(c["text"] for c in children)
    idxs = [c["child_index"] for c in children]
    chosen = set(i for i in matched_idx if i in idxs) or {idxs[0]}
    size = sum(len(c["text"]) + 1 for c in children if c["child_index"] in chosen)
    by_idx = {c["child_index"]: c for c in children}
    step = 1
    while size < cap and step <= len(idxs):
        grew = False
        for cand in (min(chosen) - step, max(chosen) + step):
            if cand in by_idx and cand not in chosen:
                add = len(by_idx[cand]["text"]) + 1
                if size + add > cap:
                    continue
                chosen.add(cand)
                size += add
                grew = True
        if not grew and step > len(idxs):
            break
        step += 1
    out, prev = [], None
    for i in sorted(chosen):
        if prev is not None and i != prev + 1:
            out.append("[...]")
        out.append(by_idx[i]["text"])
        prev = i
    return "\n".join(out)
