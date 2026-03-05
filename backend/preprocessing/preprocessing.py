from __future__ import annotations  # EN ÜSTTE OLMAK ZORUNDA!
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config.configuration import settings  # 'Settings' yerine 'settings' aldık
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Dosya yollarını güvenli hale getirelim
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# settings üzerinden küçük harfle erişiyoruz
if not settings.DOCUMENT_PATH:
    # Eğer boşsa varsayılan bir yol atayalım ki sistem çökmesin
    target_doc_path = "backend/data/Json/mevzuat_verileri.json"
else:
    target_doc_path = settings.DOCUMENT_PATH


file_path = os.path.join(BASE_DIR, "data", "Json", "mevzuat_verileri.json")


# Tabloyu metin haline getirme fonksiyonu
def format_table_as_text(table_data: list) -> str:
    if not table_data or not isinstance(table_data, list) or not isinstance(table_data[0], list):
        return ""

    headers = table_data[0]
    rows = table_data[1:]
    semantic_rows = []

    for idx, row in enumerate(rows, start=1):
        row_parts = []
        for col_idx, cell in enumerate(row):
            if col_idx < len(headers):
                header = str(headers[col_idx]).strip()
                value = str(cell).strip()
                row_parts.append(f"{header}: {value}")
        semantic_rows.append(f"SATIR {idx}:\n" + "\n".join(row_parts))

    return "\n\n".join(semantic_rows)


def verbalize_tables_with_llm(formatted_tables_text: str, model_name):
    if not formatted_tables_text.strip():
        return ""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    initial_chunks = text_splitter.split_text(formatted_tables_text)
    final_processed_chunks = []

    for chunk in initial_chunks:
        if "SATIR" in chunk or ":" in chunk:
            print("--- Tablo bölgesi LLM ile işleniyor ---")
            prompt = (
                "Sen profesyonel bir sağlık mevzuatı uzmanısın. "
                "Aşağıdaki metindeki tabloları oku ve bunları akıcı, doğal bir dile çevir:\n\n"
                f"{chunk}"
            )

            try:
                response = model_name.invoke(prompt)
                # response.content kullanımı LangChain Gemini için doğrudur
                processed_text = getattr(response, "content", str(response))
                final_processed_chunks.append(processed_text)
            except Exception as e:
                print(f"LLM İşleme Hatası: {e}")
                final_processed_chunks.append(chunk)
        else:
            final_processed_chunks.append(chunk)

    return "\n\n".join(final_processed_chunks)


def flatten_mevzuat_object(mevzuat_object: Dict[str, Any], model_name) -> str:
    flat_parts = []
    flat_parts.append(f"MEVZUAT ADI: {mevzuat_object.get('Mevzuat Adı', 'YOK')}")
    flat_parts.append(f"MEVZUAT TÜRÜ: {mevzuat_object.get('Mevzuat Türü', 'YOK')}")

    content_list = mevzuat_object.get("Mevzuat İçeriği", [])
    if isinstance(content_list, list) and content_list:
        flat_parts.append("\n".join(str(x).strip() for x in content_list))

    tables = mevzuat_object.get("Tablolar", [])
    if isinstance(tables, list) and tables:
        semantic_tables = [format_table_as_text(t) for t in tables if isinstance(t, list)]
        combined_semantic_text = "\n\n".join(semantic_tables)

        if combined_semantic_text.strip():
            print(f"--- Tablo verileri LLM'e gönderiliyor... ---")
            llm_verbalized_text = verbalize_tables_with_llm(combined_semantic_text, model_name)
            flat_parts.append("\n=== TABLO DETAYLARI VE CEZALAR ===")
            flat_parts.append(llm_verbalized_text)

    return "\n\n".join(flat_parts)