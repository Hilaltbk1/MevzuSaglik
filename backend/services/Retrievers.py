from __future__ import annotations
import os
import pickle
from typing import List, Any, Dict, Optional # Optional ekledik

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import PromptTemplate

# Buradaki import yollarını şu şekilde netleştirin:
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from backend.config.configuration import Settings
from backend.prompt.My_Prompt import create_prompt
load_dotenv()
settings = Settings()


def retrieval_chain():
    """
    LangChain'in `langchain.chains.*` yardımcılarını kullanmadan,
    kendi basit RAG zincirimizi kuruyoruz. Böylece
    `ModuleNotFoundError: langchain.chains` hatasını tamamen ortadan kaldırıyoruz.
    """
    from backend.services.Vector_store import initialize_vector_store

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    # 1. Vektör veritabanını ve doküman chunk'larını al
    v_db, split_text = initialize_vector_store(rebuild_db=False)
    if v_db is None:
        raise ValueError("Hata: Vektör veritabanı başlatılamadı! Qdrant bağlantısını kontrol et.")

    def get_bm25_retriever(split_text):
        picke_path = "/bm25_index.pkl"

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
        search_kwargs={"k": 3},
    )
    bm25_retriever = get_bm25_retriever(split_text)

    # Şimdilik ensemble yerine sadece vektör tabanlı retriever kullanıyoruz
    mix_retriever = vector_retriever

    # 3. Prompt'ları hazırla
    qa_pr, c_pr = create_prompt()

    document_prompt = PromptTemplate(
        input_variables=["page_content", "Mevzuat_Adi"],
        template="[KAYNAK: {Mevzuat_Adi}]\nİÇERİK: {page_content}",
    )

    class FullChain:
        def __init__(self, llm_client, retriever, qa_prompt, ctx_prompt, doc_prompt):
            self.llm = llm_client
            self.retriever = retriever
            self.qa_prompt = qa_prompt
            self.ctx_prompt = ctx_prompt
            self.doc_prompt = doc_prompt

        def _build_search_query(self, question: str, chat_history: List[Any]) -> str:
            try:
                history_text = "\n".join(
                    [getattr(m, "content", str(m)) for m in chat_history]
                )
                prompt = self.ctx_prompt.format(
                    input=question,
                    chat_history=history_text,
                )
                resp = self.llm.invoke(prompt)
                return getattr(resp, "content", str(resp))
            except Exception:
                # Herhangi bir hata olursa direkt orijinal soruyu kullan
                return question

        def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            question: str = inputs.get("input", "")
            chat_history: List[Any] = inputs.get("chat_history", [])

            # 1) Arama sorgusunu üret
            search_query = self._build_search_query(question, chat_history)

            # 2) İlgili dokümanları al
            docs = self.retriever.get_relevant_documents(search_query)

            # 3) Doküman içeriğini formatla
            formatted_docs = []
            for d in docs:
                text = self.doc_prompt.format(
                    page_content=d.page_content,
                    Mevzuat_Adi=d.metadata.get("Mevzuat_Adi", "Bilinmeyen"),
                )
                formatted_docs.append(text)

            context_text = "\n\n".join(formatted_docs)

            # 4) QA promptunu doldurup modelden cevap al
            qa_prompt_filled = self.qa_prompt.format(
                input=question,
                context=context_text,
            )
            answer_msg = self.llm.invoke(qa_prompt_filled)
            answer_text = getattr(answer_msg, "content", str(answer_msg))

            return {
                "answer": answer_text,
                "context": docs,
            }

    class ChainContainer:
        def __init__(self, fc):
            self.full_chain = fc

    full_chain = FullChain(
        llm_client=llm,
        retriever=mix_retriever,
        qa_prompt=qa_pr,
        ctx_prompt=c_pr,
        doc_prompt=document_prompt,
    )

    return ChainContainer(full_chain)
