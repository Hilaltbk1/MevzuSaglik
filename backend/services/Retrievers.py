import os
import pickle
from dotenv import load_dotenv
# Google AI
from langchain_google_genai import ChatGoogleGenerativeAI
# Retrievers & Core
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import PromptTemplate
from langchain.retrievers.ensemble import EnsembleRetriever
# Chains (0.2.x Uyumlu Yeni Adresler)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain

from backend.config.configuration import Settings
from backend.prompt.My_Prompt import create_prompt
# ------------------------------

load_dotenv()  # En başa taşıdık
settings = Settings()
# Satır 2 civarındaki hata için:
def retrieval_chain():
    from backend.services.Vector_store import initialize_vector_store

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    #vector_store,chunks
    v_db,split_text=initialize_vector_store(rebuild_db=False)
    if v_db is None:
        raise ValueError("Hata: Vektör veritabanı başlatılamadı! Qdrant bağlantısını kontrol et.")

    def get_bm25_retriever(split_text):
        picke_path="/bm25_index.pkl"

        if os.path.exists(picke_path):
            with open(picke_path, "rb") as f:
                return pickle.load(f)
        else:
            print("B25 kaydediliyor...")
            bm25=BM25Retriever.from_documents(split_text)
            with open(picke_path, "wb") as f:
                pickle.dump(bm25, f)
            return bm25

    #vector search
    vector_retrievers=v_db.as_retriever(search_type="similarity",search_kwargs={
        "k": 3,
         })
    # BM25
    bm25_retrievers=get_bm25_retriever(split_text)
    mix_retrievers=EnsembleRetriever(retrievers=[vector_retrievers,bm25_retrievers],weights=[0.5,0.5])

    # 5. Final Retrieval Chain
    qa_pr,c_pr = create_prompt()

    document_prompt = PromptTemplate(
        input_variables=["page_content", "Mevzuat_Adi"],
        template="[KAYNAK: {Mevzuat_Adi}]\nİÇERİK: {page_content}"
    )

    history_aware_retriever=create_history_aware_retriever(
        llm,
        mix_retrievers,
        c_pr
    )


    #okuma ve cevaplama -llm ı beslemek
    question_answer_chain = create_stuff_documents_chain(llm,qa_pr,document_variable_name="context", document_prompt=document_prompt)



    full_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    class ChainContainer:
        def __init__(self, fc):
            self.full_chain = fc


    return ChainContainer(full_chain)

