import json
from pathlib import Path
from typing import Dict, Any
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from config.configuration import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter



if not settings.DOCUMENT_PATH:
    raise ValueError("DOCUMENT_PATH .env dosyasında tanımlı değil")


file_path = Path(settings.DOCUMENT_PATH)

if not file_path.exists():
    raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")


def format_table_as_text(table_data: list) -> str:
    """İç içe listelenmiş tablo verilerini sütunları hizalanmış düz metin tabloya dönüştürür."""
    if not table_data or not isinstance(table_data[0], list):
        return ""

    # 1. Her sütundaki maksimum genişliği bul
    try:
        num_cols = max(len(row) for row in table_data)
    except ValueError:
        # Eğer tablo boşsa veya satırlar liste değilse (ki bu kontrol edilmeli)
        return ""

    col_widths = [0] * num_cols

    for row in table_data:
        # Satırın num_cols'tan kısa olması durumunu yönet
        if len(row) < num_cols:
            row.extend([''] * (num_cols - len(row)))

        for i, cell in enumerate(row):
            # Satır sonlarını tek boşluğa çevir (hizalamayı bozmamak için)
            cell_str = str(cell).replace('\n', ' ').strip()
            if len(cell_str) > col_widths[i]:
                col_widths[i] = len(cell_str)

    # 2. Tabloyu metin olarak formatla
    formatted_rows = []

    # Başlıkları ve ayıracı ekle
    header = table_data[0]
    # range(len(header)) kullanıldı
    formatted_header = " | ".join(str(header[i]).ljust(col_widths[i]) for i in range(len(header)))
    formatted_rows.append(formatted_header)
    formatted_rows.append("-" * len(formatted_header))

    # Veri satırlarını ekle
    for row in table_data[1:]:
        # ljust ile hizalanmış satırı oluştur
        formatted_row_str = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        formatted_rows.append(formatted_row_str)  # Listeye dizeyi ekle

    return "\n".join(formatted_rows)


def flatten_mevzuat_object(mevzuat_object: Dict[str, Any]) -> str:
    """Tek bir mevzuat objesini düz metne çevirir"""

    flat_parts = []

    # Temel bilgiler
    flat_parts.append(f"MEVZUAT ADI: {mevzuat_object.get('Mevzuat Adı', 'YOK')}")
    flat_parts.append(f"MEVZUAT TÜRÜ: {mevzuat_object.get('Mevzuat Türü', 'YOK')}")

    # İçerik
    content_list = mevzuat_object.get("Mevzuat İçeriği", [])
    if isinstance(content_list, list) and content_list:
        flat_parts.append("\n".join(str(x).strip() for x in content_list))

    # Tabloları formatlayarak ekle (Düzeltilmiş liste anlama ve tip kontrolü)
    tables = mevzuat_object.get("Tablolar", [])
    if isinstance(tables, list) and tables:
        # Tablo verisinin liste (satırlar) listesi olduğunu varsayarak kontrol ediyoruz
        formatted_tables = [format_table_as_text(t) for t in tables if isinstance(t, list)]
        flat_parts.append("==================== TABLOLAR ====================")
        flat_parts.append("\n\n".join(ft for ft in formatted_tables if ft))

    return "\n\n".join(flat_parts)

