import sys
from pathlib import Path
import re
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# =========================
# PATH & ENV
# =========================
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

from utils import llm_client
from prompts.judge_prompt import JUDGE_PROMPT

tqdm.pandas()
load_dotenv()

# =========================
# FILE PATHS
# =========================
path_golden = r"C:\Users\hilal\MevzuSaglik\evaluation\data\processed\cleaned_synthetic_dataset.json"
path_rag_results = r"C:\Users\hilal\MevzuSaglik\evaluation\data\processed\rag_test_result.json"

# =========================
# LOAD & MERGE DATA
# =========================
print("📊 Veri setleri yükleniyor...")

golden_df = pd.read_json(path_golden)
rag_df = pd.read_json(path_rag_results)

evaluation_df = pd.merge(golden_df, rag_df, on=["chunk_id", "question"])

evaluation_df = evaluation_df.rename(columns={
    "question": "user_input",
    "ground_truth": "reference",
    "rag_answer": "response",
    "retrieved_content": "retrieved_contexts"
})

if evaluation_df.empty:
    raise ValueError("❌ Veri setleri birleştirilemedi!")

print("veri setleri birleştirildi")
print(evaluation_df.columns)

# =========================
# SAFE LLM JUDGE (HF UYUMLU)
# =========================
def safe_llm_judge(x, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = llm_client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": JUDGE_PROMPT.format(
                            question=x["user_input"],
                            answer=x["response"],
                            reference_answer=x["reference"],
                            context="\n".join(x["retrieved_contexts"])
                        )
                    }
                ],
                max_tokens=800   # ✅ HF InferenceClient uyumlu
            )

            # 🔴 KRİTİK: STRING ÇIKART
            return response["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"⚠️ Retry {attempt + 1}/{max_retries}: {e}")
            time.sleep(2)  # basit ve stabil backoff

    return "ERROR: LLM judge failed"

# =========================
# APPLY
# =========================
evaluation_df["llm_judge"] = evaluation_df.progress_apply(
    safe_llm_judge,
    axis=1
)

# =========================
# SCORE EXTRACTION
# =========================
def extract_judge_score(answer: str) -> float:
    try:
        if not isinstance(answer, str):
            return 0.0

        # SADECE "Toplam puan" geçen satırı al
        for line in answer.splitlines():
            if "Toplam puan" in line:
                match = re.search(r"\b([0-9]|10)(?:\.\d+)?\b", line)
                if match:
                    return float(match.group(0))

        return 0.0
    except Exception:
        return 0.0


evaluation_df["llm_judge_score"] = evaluation_df["llm_judge"].apply(extract_judge_score)

print("MAX SCORE:", evaluation_df["llm_judge_score"].max())

# =========================
# FINAL SCORE
# =========================
evaluation_df["final_score"] = (
    evaluation_df["llm_judge_score"]
    .clip(0, 10)
)

# =========================
# REPORT
# =========================
print("\n📊 LLM Judge Score Summary:")
print(evaluation_df["llm_judge_score"].describe())

print(f"\n✅ {len(evaluation_df)} kayıt başarıyla değerlendirildi.")

# =========================
