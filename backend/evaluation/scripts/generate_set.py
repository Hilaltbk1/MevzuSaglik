import json
import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import random

# 1. Ortam değişkenlerini yükle
load_dotenv()

# sys.path ayarları
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

# Services importu
from backend.services.Vector_store import initialize_vector_store

# Veritabanını başlat
print("⚙️ Veritabanına bağlanılıyor...", flush=True)
vs, chunks = initialize_vector_store(rebuild_db=False)
print(f"✅ Veritabanı hazır. Toplam {len(chunks)} parça bulundu.", flush=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_prompt_template(file_name):
    """Prompt dosyasını okuyan yardımcı fonksiyon"""
    path = root_path / "evaluation" / "prompts" / file_name
    # 'f' yerine 'file' kullanarak shadowing uyarısını giderdik
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

def call_llm(system_instructions: str, context_data: str):
    """GPT-4o-mini çağrısı yapan fonksiyon"""
    print("📡 OpenAI (GPT-4o-mini) sunucusuna istek gönderildi...", flush=True)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": f"Bağlam: {context_data}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            timeout=30.0
        )
        return response.choices[0].message.content
    except Exception as err:
        # 'e' yerine 'err' kullanarak shadowing uyarısını giderdik
        print(f"❌ OpenAI Çağrısı Başarısız: {str(err)}", flush=True)
        return None

# --- ANA SÜREÇ ---

try:
    QATEMPLATE = load_prompt_template("qa_generation.txt")
except Exception as template_err:
    print(f"❌ Prompt dosyası yüklenemedi: {template_err}")
    sys.exit(1)

synthetic_data = []
sample_size = 100
selected_chunks = random.sample(chunks, sample_size)

for i, chunk in enumerate(selected_chunks):
    print(f"\n{i + 1}/{sample_size}. parça işleniyor...", flush=True)

    content = getattr(chunk, 'page_content', str(chunk))
    llm_response = call_llm(QATEMPLATE, content)

    if llm_response:
        try:
            res_data = json.loads(llm_response)

            if isinstance(res_data, list):
                parsed_list = res_data
            else:
                parsed_list = next((v for v in res_data.values() if isinstance(v, list)), [])

            for pair in parsed_list:
                print(f"   -> Soru kaydediliyor: {pair.get('soru', '')[:30]}...")
                synthetic_data.append({
                    "chunk_id": i,
                    "question": pair.get("soru"),
                    "answer": pair.get("cevap"),
                })



        except Exception as json_err:
            print(f"❌ JSON İşleme Hatası: {json_err}")

# --- SONUÇLARI KAYDET (Girintileme hataları düzeltildi) ---
output_path = root_path / "evaluation" / "data" / "processed" / "synthetic_dataset.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as final_file:
    json.dump(synthetic_data, fp=final_file, ensure_ascii=False, indent=4)

print(f"\n🚀 Başarıyla bitti! {len(synthetic_data)} soru kaydedildi: {output_path}")