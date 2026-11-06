"""MevzuSağlık için yapı duyarlı Parent-Child chunking.

build_chunks() child Chunk listesi döndürür. Aynı parent_id değerine sahip
child kayıtları retrieval sırasında assemble_parent() ile birleştirilebilir.
Bu modül Qdrant/API/DB bağlantısı kurmaz.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from backend.services.text_utils import normalize_madde_no

PARENT_MAX = 4000
CHILD_MAX = 900
CHILD_MIN = 200

_HEADER_RE = re.compile(r"^\s*MEVZUAT\s+(?:ADI|TÜRÜ)\s*:", re.I)
_MADDE_RE = re.compile(
    r"^\s*(?:(?P<pre>Geçici|Ek)\s+)?Madde\s+"
    r"(?P<no>\d{1,4}(?:\s*/\s*[A-Za-zÇĞİÖŞÜ])?)"
    r"(?=\s|[-–—.:(]|$)", re.I
)
_BOLUM_RE = re.compile(
    r"^\s*(?:(?:[IVXLCDM]+|\d+)\s*[-.]?\s*)?(?:BÖLÜM|KISIM)\b.*$", re.I
)
_EK_RE = re.compile(
    r"^\s*EK\s*[-–]?\s*(?P<no>\d{1,3}|[A-ZÇĞİÖŞÜ])(?=\s|[-–:.]|$)", re.I
)
_FIKRA_RE = re.compile(r"^\s*\((\d{1,3})\)\s*")
_NUM_HEAD_RE = re.compile(
    r"^\s*(?P<num>\d{1,2}(?:\.\d{1,2}){0,3})[.)]?\s+"
    r"(?P<title>[^\n]{2,90})\s*$"
)
_TABLE_PREFIXES = ("TABLO", "ÇİZELGE", "TOPLAM", "AÇIKLAMA", "SIRA NO")


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def doc_key_for(title: str, salt: str = "") -> str:
    return hashlib.sha1(f"{salt}|{title}".encode("utf-8")).hexdigest()[:12]


def _clean_text(text: str) -> str:
    text = (text or "").replace("\x00", " ").replace("\r\n", "\n")
    text = text.replace("\r", "\n").replace("\u00a0", " ").replace("\ufeff", "")
    lines = [re.sub(r"[ \t]+$", "", line) for line in text.split("\n")]
    result, blanks = [], 0
    for line in lines:
        if not line.strip():
            blanks += 1
            if blanks <= 2:
                result.append("")
        else:
            blanks = 0
            result.append(line)
    return "\n".join(result).strip()


def _number(value: str) -> int:
    match = re.match(r"\d+", normalize_madde_no(value) or value)
    return int(match.group()) if match else 0


def madde_label(meta: Dict[str, Any]) -> str:
    if meta.get("kind") == "ek" and meta.get("ek_no"):
        return f"Ek-{meta['ek_no']}"
    no = meta.get("madde_no")
    if not no:
        return meta.get("section_title") or ""
    tur = str(meta.get("madde_tur") or "").upper()
    prefix = "Geçici Madde " if tur == "G" else "Ek Madde " if tur == "E" else "Madde "
    label = prefix + str(no)
    if meta.get("madde_title"):
        label += f" ({meta['madde_title']})"
    return label


def source_label(meta: Dict[str, Any]) -> str:
    name = meta.get("Mevzuat_Adi") or "Bilinmeyen"
    label = madde_label(meta)
    return f"{name}, {label}" if label else name


def contextual_text(meta: Dict[str, Any], body: str) -> str:
    parts = [meta.get("Mevzuat_Adi") or "", meta.get("bolum") or "", madde_label(meta)]
    header = " > ".join(str(p).strip() for p in parts if p)
    return f"[{header}]\n{body}" if header else body


def _split_long_line(line: str, limit: int) -> List[str]:
    """Uzun satırı önce cümle, sonra kelime sınırından böler."""
    if len(line) <= limit:
        return [line]
    result, current = [], ""
    sentences = re.split(r"(?<=[.!?;:])\s+", line.strip())
    for sentence in sentences:
        if len(sentence) > limit:
            if current:
                result.append(current)
                current = ""
            part = ""
            for word in sentence.split():
                if len(word) > limit:
                    if part:
                        result.append(part)
                        part = ""
                    result.extend(word[i:i + limit] for i in range(0, len(word), limit))
                elif part and len(part) + 1 + len(word) > limit:
                    result.append(part)
                    part = word
                else:
                    part = f"{part} {word}".strip()
            if part:
                result.append(part)
        elif current and len(current) + 1 + len(sentence) > limit:
            result.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        result.append(current)
    return result


def _pack(text: str, limit: int) -> List[str]:
    if limit <= 0:
        raise ValueError("Chunk limiti pozitif olmalıdır.")
    result, current = [], ""
    for line in text.split("\n"):
        pieces = _split_long_line(line.strip(), limit) if line.strip() else [""]
        for piece in pieces:
            candidate = f"{current}\n{piece}" if current else piece
            if current and len(candidate) > limit:
                result.append(current)
                current = piece
            else:
                current = candidate
    if current:
        result.append(current)
    return [part for part in result if part.strip()]


def _is_title_line(line: str) -> bool:
    value = line.strip()
    if not value or len(value) > 100 or len(value.split()) > 12:
        return False
    if value[-1:] in ".,;:" or _MADDE_RE.match(value) or _BOLUM_RE.match(value):
        return False
    if any(value.upper().startswith(prefix) for prefix in _TABLE_PREFIXES):
        return False
    return value[0].isupper()


def parse_units(text: str) -> List[Dict[str, Any]]:
    """Madde başlangıçlarını ayırır; sıra dışı numaraları otomatik kabul etmez."""
    lines = _clean_text(text).split("\n")
    while lines and (not lines[0].strip() or _HEADER_RE.match(lines[0])):
        lines.pop(0)

    units = [{
        "madde_no": None, "madde_tur": None, "title": None,
        "bolum": None, "lines": [],
    }]
    section, last_number = None, None

    for line in lines:
        value = line.strip()
        if value and _BOLUM_RE.match(value):
            section = value
            units[-1]["lines"].append(line)
            continue

        match = _MADDE_RE.match(line)
        accepted, number_text, number, prefix = False, None, 0, None
        if match:
            prefix = match.group("pre")
            number_text = normalize_madde_no(match.group("no"))
            number = _number(number_text)
            if prefix:
                accepted = True
            elif last_number is None:
                accepted = 1 <= number <= 100
            else:
                accepted = last_number < number <= last_number + 100

        if not accepted:
            units[-1]["lines"].append(line)
            continue

        previous = units[-1]["lines"]
        while previous and not previous[-1].strip():
            previous.pop()
        title = previous.pop().strip() if previous and _is_title_line(previous[-1]) else None
        madde_tur = None
        if prefix:
            madde_tur = "G" if prefix.casefold() == "geçici" else "E"
        else:
            last_number = number
        units.append({
            "madde_no": number_text, "madde_tur": madde_tur,
            "title": title, "bolum": section, "lines": [line],
        })
    return units


def _is_upper_heading(line: str) -> bool:
    value = line.strip()
    letters = [char for char in value if char.isalpha()]
    if not 5 <= len(value) <= 90 or len(letters) < 5:
        return False
    if value[-1:] in ".,;:" or _MADDE_RE.match(value) or _BOLUM_RE.match(value):
        return False
    if any(value.upper().startswith(prefix) for prefix in _TABLE_PREFIXES):
        return False
    if sum(char.isdigit() for char in value) > max(3, len(value) // 3):
        return False
    return sum(char.isupper() for char in letters) / len(letters) >= 0.82


def detect_structure(text: str, type_hint: Optional[str] = None) -> Dict[str, Any]:
    cleaned = _clean_text(text)
    units = parse_units(cleaned)
    numbers = [_number(u["madde_no"]) for u in units if u.get("madde_no") and not u.get("madde_tur")]
    gaps = sum(1 for a, b in zip(numbers, numbers[1:]) if b > a + 3)
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    headings = [
        line for line in lines
        if _NUM_HEAD_RE.match(line) or _is_upper_heading(line) or _BOLUM_RE.match(line)
    ]
    hint = (type_hint or "").casefold()

    if len(numbers) >= 3 and gaps <= max(2, len(numbers) // 4):
        kind = "madde"
    elif len(headings) >= 3 or ("rehber" in hint and len(headings) >= 2):
        kind = "baslikli"
    else:
        kind = "duz"

    return {
        "kind": kind, "madde_count": len(numbers), "madde_gaps": gaps,
        "heading_count": len(headings), "length": len(cleaned),
    }


def _merge_tiny_units(units: List[Dict[str, Any]], minimum: int = CHILD_MIN):
    result = []
    for unit in units:
        current = dict(unit)
        if result and len("\n".join(current["lines"]).strip()) < minimum:
            result[-1]["lines"].extend(current["lines"])
            if current.get("section_title"):
                result[-1]["section_title"] = current["section_title"]
                result[-1]["bolum"] = current.get("bolum") or result[-1].get("bolum")
        else:
            result.append(current)
    return result


def parse_heading_units(text: str) -> List[Dict[str, Any]]:
    lines = _clean_text(text).split("\n")
    while lines and (not lines[0].strip() or _HEADER_RE.match(lines[0])):
        lines.pop(0)
    units = [{
        "madde_no": None, "madde_tur": None, "title": None,
        "bolum": None, "section_title": None, "lines": [],
    }]
    stack: List[Tuple[int, str]] = []

    for line in lines:
        value = line.strip()
        match = _NUM_HEAD_RE.match(value) if value else None
        depth, title = None, None
        if match:
            depth = match.group("num").count(".") + 1
            title = f"{match.group('num')} {match.group('title').strip()}"
        elif value and _is_upper_heading(value):
            depth, title = 1, value

        if title and depth is not None:
            while stack and stack[-1][0] >= depth:
                stack.pop()
            stack.append((depth, title))
            path = " > ".join(item[1] for item in stack)
            units.append({
                "madde_no": None, "madde_tur": None, "title": None,
                "bolum": path, "section_title": title, "lines": [line],
            })
        else:
            units[-1]["lines"].append(line)
    return _merge_tiny_units(units)


def _split_fikra(text: str, limit: int) -> List[Tuple[str, Optional[str]]]:
    segments, current, current_no = [], [], None
    for line in text.split("\n"):
        match = _FIKRA_RE.match(line)
        if match and current:
            segments.append(("\n".join(current), current_no))
            current, current_no = [line], match.group(1)
        else:
            if match:
                current_no = match.group(1)
            current.append(line)
    if current:
        segments.append(("\n".join(current), current_no))

    if sum(1 for _, no in segments if no) < 2:
        return [(part, None) for part in _pack(text, limit)]

    result, buffer, numbers = [], "", []

    def number_label():
        if not numbers:
            return None
        return f"{numbers[0]}-{numbers[-1]}" if len(numbers) > 1 else numbers[0]

    for segment, number in segments:
        for piece in _pack(segment, limit):
            candidate = f"{buffer}\n{piece}" if buffer else piece
            if buffer and len(candidate) > limit:
                result.append((buffer, number_label()))
                buffer, numbers = piece, ([number] if number else [])
            else:
                buffer = candidate
                if number and number not in numbers:
                    numbers.append(number)
    if buffer:
        result.append((buffer, number_label()))
    return result


def _split_eks(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for unit in units:
        current = dict(unit, lines=[])
        for line in unit["lines"]:
            value = line.strip()
            match = _EK_RE.match(value)
            standalone = (
                match is not None and len(value) <= 100
                and (value.isupper() or len(value.split()) <= 5)
            )
            if standalone:
                if current["lines"]:
                    result.append(current)
                current = {
                    "madde_no": None, "madde_tur": None, "title": value,
                    "bolum": unit.get("bolum"), "section_title": None,
                    "ek_no": match.group("no"), "lines": [line],
                }
            else:
                current["lines"].append(line)
        if current["lines"]:
            result.append(current)
    return result


def build_chunks(
    doc_text: str,
    base_meta: Dict[str, Any],
    *,
    doc_key: str,
    parent_max: int = PARENT_MAX,
    child_max: int = CHILD_MAX,
    type_hint: Optional[str] = None,
) -> List[Chunk]:
    if parent_max <= 0 or child_max <= 0 or child_max > parent_max:
        raise ValueError("Limitler pozitif olmalı ve child_max <= parent_max olmalıdır.")
    text = _clean_text(doc_text)
    if not text:
        return []

    profile = detect_structure(text, type_hint or base_meta.get("Mevzuat_Türü"))
    structure = profile["kind"]
    if structure == "madde":
        units = _split_eks(parse_units(text))
    elif structure == "baslikli":
        units = parse_heading_units(text)
    else:
        units = [{
            "madde_no": None, "madde_tur": None, "title": None,
            "bolum": None, "section_title": None, "lines": text.split("\n"),
        }]

    chunks: List[Chunk] = []
    for unit_index, unit in enumerate(units):
        body = "\n".join(unit.get("lines", [])).strip()
        if not body:
            continue

        if unit.get("ek_no"):
            unit_id, unit_kind = f"EK{unit['ek_no']}", "ek"
        elif unit.get("madde_no"):
            unit_id, unit_kind = f"{unit.get('madde_tur') or 'M'}{unit['madde_no']}", "madde"
        elif unit.get("section_title"):
            unit_id, unit_kind = f"baslik{unit_index}", "blok"
        elif unit_index == 0 and structure != "duz":
            unit_id, unit_kind = "giris", "giris"
        else:
            unit_id, unit_kind = f"blok{unit_index}", "blok"

        for parent_index, parent_text in enumerate(_pack(body, parent_max)):
            parent_id = f"{doc_key}:{unit_id}:{parent_index}"
            children = (
                _split_fikra(parent_text, child_max)
                if unit_kind == "madde"
                else [(part, None) for part in _pack(parent_text, child_max)]
            )
            merged: List[Tuple[str, Optional[str]]] = []
            for child_text, paragraph in children:
                if merged and len(child_text) < CHILD_MIN and (
                    len(merged[-1][0]) + 1 + len(child_text) <= child_max
                ):
                    old, old_paragraph = merged[-1]
                    merged[-1] = (old + "\n" + child_text, old_paragraph or paragraph)
                else:
                    merged.append((child_text, paragraph))

            for child_index, (child_text, paragraph) in enumerate(merged):
                meta = dict(base_meta)
                meta.update({
                    "doc_key": doc_key, "parent_id": parent_id,
                    "child_index": child_index, "child_count": len(merged),
                    "chunk_id": f"{parent_id}:{child_index}",
                    "kind": unit_kind, "structure": structure,
                })
                if unit.get("madde_no"):
                    meta["madde_no"] = unit["madde_no"]
                if unit.get("madde_tur"):
                    meta["madde_tur"] = unit["madde_tur"]
                if unit.get("ek_no"):
                    meta["ek_no"] = unit["ek_no"]
                if unit.get("title"):
                    meta["madde_title"] = unit["title"]
                if unit.get("section_title"):
                    meta["section_title"] = unit["section_title"]
                if unit.get("bolum"):
                    meta["bolum"] = unit["bolum"]
                if paragraph:
                    meta["fikra"] = paragraph
                meta["source_label"] = source_label(meta)
                chunks.append(Chunk(text=child_text, metadata=meta))

    flags = validate_chunks(text, chunks, profile)
    for chunk in chunks:
        chunk.metadata["needs_review"] = bool(flags)
    if chunks:
        chunks[0].metadata["review_flags"] = flags
    return chunks


def validate_chunks(text: str, chunks: Sequence[Chunk], profile: Dict[str, Any]) -> List[str]:
    """Gerçek kalite sorunlarını işaretler; tek başına child sayısını hata saymaz."""
    if not chunks:
        return ["bos_cikti"]
    flags = []
    source_len = len(re.sub(r"\s+", "", _clean_text(text)))
    output_len = sum(len(re.sub(r"\s+", "", chunk.text)) for chunk in chunks)

    if source_len and output_len < source_len * 0.80:
        flags.append("kapsam_dusuk")
    if source_len and output_len > source_len * 1.35:
        flags.append("olasi_tekrar")

    small = sum(1 for chunk in chunks if len(chunk.text.strip()) < 80)
    if len(chunks) >= 8 and small / len(chunks) > 0.30:
        flags.append("cok_kucuk_chunk")
    if profile.get("kind") == "madde" and profile.get("madde_gaps", 0) > 2:
        flags.append("madde_numarasi_atlamasi")
    if profile.get("kind") == "duz" and profile.get("length", 0) > 20000:
        flags.append("uzun_belgede_yapi_bulunamadi")
    if profile.get("kind") == "baslikli" and profile.get("heading_count", 0) > max(
        3, profile.get("length", 0) / 150
    ):
        flags.append("asiri_baslik_algisi")

    # 12 child sınırı kaldırıldı. Parent büyüklüğü ayrıca izlenir.
    parent_sizes: Dict[str, int] = {}
    for chunk in chunks:
        pid = chunk.metadata.get("parent_id")
        if pid:
            parent_sizes[pid] = parent_sizes.get(pid, 0) + len(chunk.text)
    if parent_sizes and max(parent_sizes.values()) > PARENT_MAX * 1.20:
        flags.append("parent_boyutu_limit_asimi")

    ids = [chunk.metadata.get("chunk_id") for chunk in chunks]
    if len(ids) != len(set(ids)):
        flags.append("tekrarlanan_chunk_id")
    return list(dict.fromkeys(flags))


def assemble_parent(children: List[Dict[str, Any]], matched_idx: set[int], cap: int) -> str:
    """Eşleşen child'lar ve sığan komşularıyla parent bağlamı oluşturur."""
    if cap <= 0 or not children:
        return ""
    ordered = sorted(children, key=lambda item: item["child_index"])
    by_index = {item["child_index"]: item for item in ordered}
    indexes = list(by_index)
    chosen = {index for index in matched_idx if index in by_index} or {indexes[0]}

    def size(selected):
        return sum(len(by_index[i]["text"]) for i in selected) + max(0, len(selected) - 1)

    distance = 1
    while distance <= len(indexes):
        candidates = sorted({
            neighbor for index in chosen
            for neighbor in (index - distance, index + distance)
            if neighbor in by_index and neighbor not in chosen
        })
        added = False
        for candidate in candidates:
            if size(chosen | {candidate}) <= cap:
                chosen.add(candidate)
                added = True
        if not added and not candidates:
            break
        distance += 1

    result, previous = [], None
    for index in sorted(chosen):
        if previous is not None and index != previous + 1:
            result.append("[... bağlam atlandı ...]")
        result.append(by_index[index]["text"])
        previous = index
    return "\n".join(result)
