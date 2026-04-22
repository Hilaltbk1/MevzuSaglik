import os
import sys
import json
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# --- 1. PROJE KÖK DİZİNİNİ EKLE ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

from backend.services.Retrievers import retrieval_chain

load_dotenv()
DATA_DIR = BASE_DIR / "backend" / "evaluation" / "data" / "processed"

def run_evaluation_inference():
    input_path = DATA_DIR / "cleaned_synthetic_dataset.json"
    output_path = DATA_DIR / "rag_test_result.json"

    if not input_path.exists():
        print(f"❌ Hata: Girdi dosyası bulunamadı: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        golden_data = json.load(f)

    print(f"📊 Girdi dosyası yüklendi. Toplam soru sayısı: {len(golden_data)}")

    # retrieval_chain() ChainContainer nesnesini döndürüyor, içindeki full_chain'i almalıyız
    try:
        print("🔗 RAG Zinciri başlatılıyor...")
        container = retrieval_chain()
        chain = container.full_chain
        print("✅ RAG Zinciri başarıyla başlatıldı.")
    except Exception as e:
        print(f"❌ RAG Zinciri başlatılamadı: {e}")
        return

    results = []
    print(f"🚀 Test başlatılıyor...")

    max_retries = 3
    for i in tqdm(golden_data):
        question = i.get("question", "")
        if not question:
            print("⚠️ Boş soru atlanıyor...")
            continue
        
        success = False
        for attempt in range(max_retries):
            try:
                # chain.invoke hem input hem de chat_history bekliyor
                response = chain.invoke({"input": question, "chat_history": []})
                
                if response and "answer" in response:
                    results.append({
                        "chunk_id": i.get("chunk_id"),
                        "question": question,
                        "reference_answer": i.get("ground_truth", ""),
                        "rag_answer": response.get("answer", ""),
                        "retrieved_content": [doc.page_content for doc in response.get("context", [])]
                    })
                    success = True
                    break # Başarılı, döngüden çık
                else:
                    print(f"⚠️ Yanıt alınamadı veya format hatalı: {question}")
                    break # Format hatalıysa tekrar deneme anlamlı olmayabilir
            except Exception as e:
                if "getaddrinfo failed" in str(e) or "connection" in str(e).lower():
                    wait_time = (attempt + 1) * 10 # 10, 20, 30 saniye bekle
                    print(f"⚠️ Ağ/DNS hatası (Deneme {attempt + 1}/{max_retries}): {wait_time} sn bekleniyor...")
                    import time
                    time.sleep(wait_time) 
                else:
                    print(f"❌ HATA ({question}): {str(e)}")
                    break # Diğer hatalarda (mantıksal vb.) tekrar deneme

    # Çıktıları kaydet
    print(f"📝 Toplam {len(results)} sonuç kaydediliyor...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"\n✅ İşlem tamamlandı. Sonuçlar kaydedildi: {output_path}")

if __name__ == "__main__":
    run_evaluation_inference()