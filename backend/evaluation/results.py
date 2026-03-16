import sys
import os
import re
import time
import pandas as pd
from typing import Dict, Any
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# =========================
# PATH & ENV
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from backend.llm_client import llm_client
from backend.evaluation.prompts.judge_prompt import JUDGE_PROMPT

tqdm.pandas()
load_dotenv()

# =========================
# FILE PATHS
# =========================
DATA_DIR = BASE_DIR / "backend" / "evaluation" / "data" / "processed"
path_golden = DATA_DIR / "cleaned_synthetic_dataset.json"
path_rag_results = DATA_DIR / "rag_test_result.json"

# =========================
# LOAD & MERGE DATA
# =========================
if not path_golden.exists() or not path_rag_results.exists():
    print(f"❌ Hata: Veri dosyaları bulunamadı! \nGolden: {path_golden}\nResults: {path_rag_results}")
    sys.exit(1)

print("📊 Veri setleri yükleniyor...")
golden_df = pd.read_json(path_golden)
rag_df = pd.read_json(path_rag_results)

# chunk_id ve question üzerinden birleştir
# Eğer bir dosyada chunk_id eksikse sadece question üzerinden birleştir
on_cols = ["question"]
if "chunk_id" in golden_df.columns and "chunk_id" in rag_df.columns:
    on_cols.append("chunk_id")

evaluation_df = pd.merge(golden_df, rag_df, on=on_cols)

evaluation_df = evaluation_df.rename(columns={
    "question": "user_input",
    "ground_truth": "reference",
    "rag_answer": "response",
    "retrieved_content": "retrieved_contexts"
})

if evaluation_df.empty:
    raise ValueError("❌ Veri setleri birleştirilemedi!")

print(f"✅ {len(evaluation_df)} kayıt başarıyla birleştirildi.")

# =========================
# SAFE LLM JUDGE
# =========================
def safe_llm_judge(row, max_retries=5):
    # Eğer bu satır zaten değerlendirilmişse tekrar sorma (Hızlandırma ve hata önleme)
    if "llm_judge" in row and pd.notna(row["llm_judge"]) and "ERROR" not in str(row["llm_judge"]):
        return row["llm_judge"]

    prompt_text = JUDGE_PROMPT.format(
        question=row["user_input"],
        answer=row["response"],
        reference_answer=row["reference"],
        context="\n".join(row["retrieved_contexts"])
    )
    
    for attempt in range(max_retries):
        try:
            # Zaman aşımı ve bağlantı hataları için bekleme süresini kademeli artır
            response = llm_client.invoke(prompt_text)
            
            if hasattr(response, "content"):
                return response.content
            return str(response)

        except Exception as e:
            wait_time = (attempt + 1) * 5 # 5, 10, 15, 20, 25 saniye bekle
            if "503" in str(e) or "Timeout" in str(e) or "socket" in str(e):
                print(f"⚠️ Google API Meşgul veya Bağlantı Hatası (Deneme {attempt + 1}/{max_retries}). {wait_time} sn bekleniyor...")
                time.sleep(wait_time)
            else:
                print(f"⚠️ Beklenmedik Hata: {e}")
                time.sleep(2)

    return "ERROR: LLM judge failed"

# =========================
# APPLY WITH AUTO-SAVE
# =========================
output_path = DATA_DIR / "evaluation_final_report.csv"

# Eğer yarım kalmış bir rapor varsa oradan devam et
if output_path.exists():
    print("🔄 Yarım kalmış rapor bulundu, kaldığı yerden devam ediliyor...")
    existing_df = pd.read_csv(output_path)
    # Mevcut skorları ve değerlendirmeleri birleştir
    evaluation_df = pd.merge(evaluation_df, existing_df[["user_input", "llm_judge"]], on="user_input", how="left")
else:
    evaluation_df["llm_judge"] = None

print("⚖️ LLM Hakem değerlendirmesi başlıyor...")
for idx, row in tqdm(evaluation_df.iterrows(), total=len(evaluation_df)):
    if pd.isna(row["llm_judge"]) or "ERROR" in str(row["llm_judge"]):
        evaluation_df.at[idx, "llm_judge"] = safe_llm_judge(row)
        # Her 5 soruda bir geçici kayıt yap (Elektrik/İnternet kesintisine karşı)
        if idx % 5 == 0:
            evaluation_df.to_csv(output_path, index=False, encoding="utf-8-sig")

# =========================
# SCORE & HALLUCINATION EXTRACTION
# =========================
def analyze_judge_output(answer: str) -> Dict[str, Any]:
    res = {"score": 0.0, "is_hallucination": False}
    try:
        if not isinstance(answer, str):
            return res

        # 1. Skor Çıkarma (0-4 arası)
        patterns = [
            r"Toplam puan:\s*(\d+(\.\d+)?)",
            r"\[PUAN\]:\s*(\d+(\.\d+)?)",
            r"Puan:\s*(\d+(\.\d+)?)",
            r"Score:\s*(\d+(\.\d+)?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, answer, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                if score <= 4.0:
                    res["score"] = score
                    break
                elif score > 4.0 and score <= 10.0:
                    res["score"] = (score / 10.0) * 4.0
                    break
        
        # Eğer skor hala 0.0 ise son satırlara bak
        if res["score"] == 0.0:
            lines = answer.strip().splitlines()
            for line in reversed(lines[-3:]):
                numbers = re.findall(r"(\d+(\.\d+)?)", line)
                if numbers:
                    score = float(numbers[-1][0])
                    if score <= 4.0:
                        res["score"] = score
                        break

        # 2. Halüsinasyon Kontrolü
        # Judge metni içinde "hallüsinasyon", "uydurma", "uydurmuş", "kaynak dışı" gibi kelimeler geçiyor mu?
        # Ayrıca puanı 1 veya 2 ise halüsinasyon olma ihtimali yüksektir.
        hallucination_keywords = ["hallüsinasyon", "uydurma", "uydurmuş", "uydurduğu", "kaynak dışı", "bağlam dışı", "hallucination"]
        if any(word in answer.lower() for word in hallucination_keywords) and res["score"] <= 2.5:
            res["is_hallucination"] = True
            
    except:
        pass
    return res

# Değerlendirmeleri uygula
print("📊 Sonuçlar analiz ediliyor...")
analysis_results = evaluation_df["llm_judge"].apply(analyze_judge_output)
evaluation_df["score"] = analysis_results.apply(lambda x: x["score"])
evaluation_df["is_hallucination"] = analysis_results.apply(lambda x: x["is_hallucination"])

# =========================
# EXPORT & SUMMARY
# =========================
output_path = DATA_DIR / "evaluation_final_report.csv"
evaluation_df.to_csv(output_path, index=False, encoding="utf-8-sig")

total_questions = len(evaluation_df)
hallucination_count = evaluation_df["is_hallucination"].sum()
hallucination_rate = (hallucination_count / total_questions) * 100
avg_score = evaluation_df["score"].mean()

print(f"\n" + "="*30)
print(f"✨ DEĞERLENDİRME TAMAMLANDI")
print(f"Soru Sayısı: {total_questions}")
print(f"Ortalama Puan: {avg_score:.2f}/4")
print(f"Halüsinasyon Sayısı: {hallucination_count}")
print(f"Halüsinasyon Oranı: %{hallucination_rate:.1f}")
print(f"TÜBİTAK H1 Hedefi (<%20): {'✅ BAŞARILI' if hallucination_rate < 20 else '❌ BAŞARISIZ'}")
print("="*30)
print(f"📄 Detaylı rapor kaydedildi: {output_path}")