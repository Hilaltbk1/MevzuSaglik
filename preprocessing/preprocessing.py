import json
import ollama
from pathlib import Path
from typing import Dict, Any
from config.configuration import Settings
from utils import llm_client
from langchain.text_splitter import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).resolve().parent.parent

if not Settings.DOCUMENT_PATH:
    raise ValueError("DOCUMENT_PATH .env dosyasında tanımlı değil")

file_path = BASE_DIR / Settings.DOCUMENT_PATH

if not file_path.exists():
    raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

#tabloyu metin haline getirme
def format_table_as_text(table_data: list) -> str:
    if not table_data or not isinstance(table_data[0], list):
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

#tabloyu ragın anlayacagı sekle çevirme
def verbalize_tables_with_llm(formatted_tables_text: str,model_name):

    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size =3000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    initial_chunks=text_splitter.split_text(formatted_tables_text)

    final_processed_chunks = []

    for chunk in initial_chunks:

        if "|" in chunk or  "  " in chunk:

            print("Tablo tespit edildi ")
            response = model_name.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Sen profesyonel bir sağlık mevzuatı uzmanısın. Sana verilen metindeki tabloları oku ve bunları doğal dile çevir."
                    },
                    {
                        "role": "user",
                        "content": f"Aşağıdaki metindeki tabloları akıcı cümlelere dönüştür:\n\n{chunk}"
                        # KRİTİK: Burada 'prompts' değil 'chunk' (parça) gönderiyoruz!
                    }
                ],
              temperature=0
            )
            processed_text = response.choices[0].message.content
            final_processed_chunks.append(processed_text)
        else:
            # Normal metin ise hiç dokunmadan listeye ekle
            final_processed_chunks.append(chunk)

    return "\n\n".join(final_processed_chunks)

#tek bir  mevzuatları ragın anlayacagı sekle getir
def flatten_mevzuat_object(mevzuat_object: Dict[str, Any],model_name) -> str:


    flat_parts = []


    flat_parts.append(f"MEVZUAT ADI: {mevzuat_object.get('Mevzuat Adı', 'YOK')}")
    flat_parts.append(f"MEVZUAT TÜRÜ: {mevzuat_object.get('Mevzuat Türü', 'YOK')}")

    # İçerik
    content_list = mevzuat_object.get("Mevzuat İçeriği", [])
    if isinstance(content_list, list) and content_list:
        flat_parts.append("\n".join(str(x).strip() for x in content_list))

    # Tabloları formatlayarak ekle
    tables = mevzuat_object.get("Tablolar", [])
    if isinstance(tables, list) and tables:

        semantic_tables = [format_table_as_text(t) for t in tables if isinstance(t, list)]
        combined_semantic_text = "\n\n".join(semantic_tables)

        # Sadece bu kısmı LLM'e göndeririz
        print(f"--- Tablo verileri LLM'e gönderiliyor... ---")
        llm_verbalized_text = verbalize_tables_with_llm(combined_semantic_text, model_name)

        flat_parts.append("\n=== TABLO DETAYLARI VE CEZALAR ===")
        flat_parts.append(llm_verbalized_text)

    return "\n\n".join(flat_parts)



