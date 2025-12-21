import os
from dotenv import load_dotenv
# Standart ve güncel import yolları
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# Yeni import yolları
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from services.Vector_store import initialize_vector_store


# Aynı klasörde olduğun için doğrudan import et



def retrieval_chain():
    load_dotenv()
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    v_db, split_text = initialize_vector_store()

    if v_db is None:
        print("Vektör deposu yüklenemedi!")
        return None

    # 1. Retrieverları Hazırla
    vector_retriever = v_db.as_retriever(search_type="similarity", search_kwargs={'k': 5})
    bm25_retriever = BM25Retriever.from_documents(split_text)

    # 2. Hibrit Arama (Ensemble)
    mix_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )

    # 3. Sorgu Zenginleştirme (MultiQuery)
    multi_retriever = MultiQueryRetriever.from_llm(retriever=mix_retriever, llm=llm)

    # 4. Prompt Şablonu (Eksik olan kısım buydu)
    system_prompt = (
        "Sen uzman bir sağlık mevzuat asistanısın. "
        "Sana verilen bağlamı (context) kullanarak soruları yanıtla.\n\n"
        "{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 5. Zincirleri Birleştir (Hatalı olan satır burasıydı)
    # Önce döküman birleştirme zinciri (llm ve prompt alır)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    # Sonra asıl RAG zinciri (retriever ve döküman zincirini birleştirir)
    full_chain = create_retrieval_chain(multi_retriever, question_answer_chain)

    print("Zincir başarıyla oluşturuldu: aa")
    return full_chain


if __name__ == "__main__":
    retrieval_chain()