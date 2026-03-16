from __future__ import annotations
import os
import pickle
from typing import List, Any, Dict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import PromptTemplate
from backend.config.configuration import Settings
from backend.prompt.My_Prompt import create_prompt
load_dotenv()
settings = Settings()


from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from sentence_transformers.cross_encoder import CrossEncoder


def retrieval_chain():
    """
    LangChain'ev `langchain.chains.*` yardımcılarını kullanmadan,
    kendi basit RAG zincirimizi kuruyoruz. Böylece
    `ModuleNotFoundError: langchain.chains` hatasını tamamen ortadan kaldırıyoruz.
    """
    from backend.services.Vector_store import initialize_vector_store

    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME or "gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    # 1. Vektör veritabanını ve doküman chunk'larını al
    v_db, split_text = initialize_vector_store(rebuild_db=False)
    if v_db is None:
        raise ValueError("Hata: Vektör veritabanı başlatılamadı! Qdrant bağlantısını kontrol et.")

    def get_bm25_retriever(split_text):
        # Proje kök dizinindeki pkl dosyasını bulmak için:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        picke_path = os.path.join(BASE_DIR, "bm25_index.pkl")

        if os.path.exists(picke_path):
            with open(picke_path, "rb") as f:
                return pickle.load(f)
        else:
            print("B25 kaydediliyor...")
            bm25 = BM25Retriever.from_documents(split_text)
            with open(picke_path, "wb") as f:
                pickle.dump(bm25, f)
            return bm25

    # 2. Retriever'ları oluştur
    vector_retriever = v_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 15}, # Re-ranker'a daha fazla seçenek sunmak için k'yı artırdık
    )
    bm25_retriever = get_bm25_retriever(split_text)
    bm25_retriever.k = 15 # Re-ranker'a daha fazla seçenek sunmak için k'yı artırdık

    # 3. Hybrid Search (RRF) Retriever
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.documents import Document
    
    class HybridRetriever(BaseRetriever):
        v_retriever: Any
        b_retriever: Any
        
        def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
            k = 60
            v_docs = self.v_retriever.invoke(query)
            b_docs = self.b_retriever.invoke(query)
            
            scores = {}
            for rank, doc in enumerate(v_docs):
                scores[doc.page_content] = scores.get(doc.page_content, 0) + 1 / (k + rank + 1)
            for rank, doc in enumerate(b_docs):
                scores[doc.page_content] = scores.get(doc.page_content, 0) + 1 / (k + rank + 1)
            
            all_docs = {d.page_content: d for d in v_docs + b_docs}
            sorted_contents = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            
            return [all_docs[content] for content in sorted_contents]

    hybrid_retriever = HybridRetriever(v_retriever=vector_retriever, b_retriever=bm25_retriever)

    # 4. Re-Ranker Modeli Hazırlığı
    print("✨ Re-Ranker modeli yükleniyor (ilk seferde biraz sürebilir)...")
    try:
        rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    except Exception as e:
        print(f"⚠️ Re-Ranker modeli yüklenemedi, sadece Hybrid Search kullanılacak: {e}")
        rerank_model = None

    # 5. Prompt'ları hazırla
    qa_pr, c_pr = create_prompt()

    document_prompt = PromptTemplate(
        input_variables=["page_content", "Mevzuat_Adi"],
        template="[Döküman: {Mevzuat_Adi}]\nİÇERİK: {page_content}",
    )

    class FullChain:
        def __init__(self, llm_client, retriever, reranker, qa_prompt, ctx_prompt, doc_prompt):
            self.llm = llm_client
            self.retriever = retriever
            self.reranker = reranker
            self.qa_prompt = qa_prompt
            self.ctx_prompt = ctx_prompt
            self.doc_prompt = doc_prompt

        def _build_search_query(self, question: str, chat_history: List[Any]) -> str:
            try:
                history_text = "\n".join([getattr(m, "content", str(m)) for m in chat_history])
                prompt = self.ctx_prompt.format(input=question, chat_history=history_text)
                resp = self.llm.invoke(prompt)
                return getattr(resp, "content", str(resp))
            except Exception:
                return question

        def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            question: str = inputs.get("input", "")
            chat_history: List[Any] = inputs.get("chat_history", [])

            search_query = self._build_search_query(question, chat_history)
            
            # 1. Hybrid Search (RRF) sonuçlarını al (Geniş aday havuzu)
            docs = self.retriever.invoke(search_query)

            # 2. Manuel Re-Ranking (Eğer model yüklendiyse)
            if self.reranker and docs:
                try:
                    # Soru ve döküman çiftlerini hazırla
                    pairs = [[search_query, d.page_content] for d in docs]
                    # Skorları hesapla
                    rerank_scores = self.reranker.predict(pairs)
                    # Skorlarla dökümanları eşleştir ve sırala
                    scored_docs = sorted(zip(rerank_scores, docs), key=lambda x: x[0], reverse=True)
                    
                    # GÜVEN EŞİĞİ (Threshold): -1.5 altındaki dökümanları alakasız say ve ele
                    # ms-marco modellerinde genellikle -1.0 ve altı düşük alakadır.
                    # Biraz daha esnetiyoruz (-1.5) ki önemli bilgileri kaçırmayalım.
                    docs = [d for score, d in scored_docs[:6] if score > -1.5]
                    
                    if not docs:
                        print("⚠️ Re-Ranker yeterli güven puanı bulamadı, dökümanlar elendi.")
                except Exception as e:
                    print(f"⚠️ Re-ranking hatası, orijinal sıralama kullanılacak: {e}")
                    docs = docs[:6]
            else:
                docs = docs[:6]

            # 3. Formatlama ve Yanıt Üretimi
            formatted_docs = []
            for d in docs:
                text = self.doc_prompt.format(
                    page_content=d.page_content,
                    Mevzuat_Adi=d.metadata.get("Mevzuat_Adi", "Bilinmeyen"),
                )
                formatted_docs.append(text)

            context_text = "\n\n".join(formatted_docs)

            qa_prompt_filled = self.qa_prompt.format(input=question, context=context_text)
            answer_msg = self.llm.invoke(qa_prompt_filled)
            answer_text = getattr(answer_msg, "content", str(answer_msg))

            return {"answer": answer_text, "context": docs}

    class ChainContainer:
        def __init__(self, fc):
            self.full_chain = fc

    full_chain = FullChain(
        llm_client=llm,
        retriever=hybrid_retriever,
        reranker=rerank_model,
        qa_prompt=qa_pr,
        ctx_prompt=c_pr,
        doc_prompt=document_prompt,
    )

    return ChainContainer(full_chain)
