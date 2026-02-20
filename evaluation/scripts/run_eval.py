"""
Elindeki o "altın" 25 soruyu RAG sistemine (kendi koduna) sor.

Girdi: 25 soru.

İşlem: Kodun bu soruları veritabanında arar (Retrieval) ve cevap üretir (Generation).

Çıktı: Bir Excel veya JSON dosyası. İçinde şu sütunlar olsun: Soru, Sistemin Ürettiği Cevap, Referans (İdeal) Cevap.
"""
import json

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm
from services.Retrievers import retrieval_chain
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
load_dotenv()
# 1. Modelleri tanımla (Ekran görüntündeki ayarlara sadık kalarak)



def run_evaluation_inference():
    path=r"C:\Users\hilal\MevzuSaglik\evaluation\data\processed\cleaned_synthetic_dataset.json"
    with open(path,"r",encoding="utf-8") as f:
        golden_data = json.load(f)


    chain=retrieval_chain().full_chain

    results=[]

    for i in tqdm(golden_data):
        question=i["question"]

        response = chain.invoke({"input":question})
        results.append({
            "chunk_id":i["chunk_id"],
            "question":question,
            "reference_answer":i["ground_truth"],
            "rag_answer":response["answer"],
            "retrieved_content":[doc.page_content for doc in response["context"]]
        })

        #çıktıları kaydet
    o_path=r"C:\Users\hilal\MevzuSaglik\evaluation\data\processed\rag_test_result.json"
    with open(o_path,"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=4)
        print("işlem tamamlandı")

if __name__=="__main__":
    run_evaluation_inference()