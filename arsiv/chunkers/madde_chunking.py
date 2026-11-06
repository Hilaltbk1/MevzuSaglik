from __future__ import annotations

import re
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# "Madde 12", "MADDE 12 -", "Madde 12/A :"
MADDE_RE = re.compile(
    r"(?m)^\s*(?:MADDE|Madde)\s+(\d+[A-Za-z]?)\s*(?:[-–—:]|\s|$)"
)

# Satır başında (1) (2) fıkra
FIKRA_RE = re.compile(r"(?m)^\s*\((\d+)\)\s+")


def split_mevzuat_to_chunks(
    text: str,
    base_metadata: dict[str, Any],
    child_size: int = 600,
    child_overlap: int = 100,
) -> list[Document]:
    """
    1) Metni maddelere böl → her madde = parent
    2) Uzun maddeyi child chunk'lara böl (arama bunlarla)
    3) Her child metadata'sına parent_text + madde_no yaz
    """
    text = (text or "").strip()
    if not text:
        return []

    matches = list(MADDE_RE.finditer(text))

    # Madde basligi yoksa: eski karaktere yakin fallback
    if not matches:
        return _fallback_char_chunks(text, base_metadata, child_size, child_overlap)

    out: list[Document] = []

    # İlk maddeden önceki önsöz
    if matches[0].start() > 0:
        preface = text[: matches[0].start()].strip()
        if preface:
            out.extend(
                _children_from_parent(
                    parent_text=preface,
                    madde_no="ONSOZ",
                    base_metadata=base_metadata,
                    child_size=child_size,
                    child_overlap=child_overlap,
                )
            )

    for i, m in enumerate(matches):
        madde_no = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parent_text = text[start:end].strip()
        if not parent_text:
            continue
        out.extend(
            _children_from_parent(
                parent_text=parent_text,
                madde_no=madde_no,
                base_metadata=base_metadata,
                child_size=child_size,
                child_overlap=child_overlap,
            )
        )
    return out


def _children_from_parent(
    parent_text: str,
    madde_no: str,
    base_metadata: dict[str, Any],
    child_size: int,
    child_overlap: int,
) -> list[Document]:
    meta = {
        **base_metadata,
        "madde_no": str(madde_no),
        "parent_text": parent_text,  # LLM baglami
    }

    # Kisa madde: tek child = parent
    if len(parent_text) <= child_size:
        return [Document(page_content=parent_text, metadata=meta)]

    # Once fikralara ayirmayi dene
    fikra_parts = _split_fikralar(parent_text)
    if len(fikra_parts) > 1:
        docs: list[Document] = []
        for fno, ftext in fikra_parts:
            fmeta = {**meta, "fikra_no": str(fno)}
            if len(ftext) <= child_size:
                docs.append(Document(page_content=ftext, metadata=fmeta))
            else:
                docs.extend(_char_split(ftext, fmeta, child_size, child_overlap))
        return docs

    return _char_split(parent_text, meta, child_size, child_overlap)


def _split_fikralar(parent_text: str) -> list[tuple[str, str]]:
    matches = list(FIKRA_RE.finditer(parent_text))
    if len(matches) < 2:
        return []

    parts: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        head = parent_text[: matches[0].start()].strip()
        if head:
            parts.append(("0", head))

    for i, m in enumerate(matches):
        fno = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(parent_text)
        body = parent_text[start:end].strip()
        if body:
            parts.append((fno, body))
    return parts


def _char_split(
    text: str,
    meta: dict[str, Any],
    size: int,
    overlap: int,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    tmp = Document(page_content=text, metadata=meta)
    return splitter.split_documents([tmp])


def _fallback_char_chunks(
    text: str,
    base_metadata: dict[str, Any],
    size: int,
    overlap: int,
) -> list[Document]:
    meta = {
        **base_metadata,
        "madde_no": "UNKNOWN",
        "parent_text": text,
    }
    return _char_split(text, meta, size, overlap)


def documents_from_docs(doc_list: list[Document]) -> list[Document]:
    """Mevcut Document listesini madde bazli child chunk'lara cevir."""
    all_chunks: list[Document] = []
    for doc in doc_list:
        chunks = split_mevzuat_to_chunks(
            doc.page_content,
            dict(doc.metadata or {}),
        )
        all_chunks.extend(chunks)
    return all_chunks