from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.retrievers import BM25Retriever
from config.configuration import Settings
from prompt.My_Prompt import create_prompt
from services.Vector_store import initialize_vector_store
from langchain_ollama import ChatOllama #


settings=Settings()
# Satır 2 civarındaki hata için:
def retrieval_chain():
    load_dotenv()

    llm = ChatOllama(
        model="llama3.1:8b",
        temperature=0
    )

    v_db,split_text=initialize_vector_store()

    #vector search
    vector_retrievers=v_db.as_retriever(search_type="similarity",search_kwargs={"k": 3})
    # BM25
    bm25_retrievers=BM25Retriever.from_documents(split_text)
    #mix
    mix_retrievers=EnsembleRetriever(retrievers=[vector_retrievers,bm25_retrievers],weights=[0.5,0.5])

    # 5. Final Retrieval Chain
    multi_retriever = MultiQueryRetriever.from_llm(
        retriever=mix_retrievers,
        llm=llm  # Yukarıda tanımladığın ve çalışan LLM
    )


    qa_pr,c_pr = create_prompt()

    history_aware_retriever=create_history_aware_retriever(
        llm,
        multi_retriever,
        c_pr
    )


    #okuma ve cevaplama -llm ı beslemek
    question_answer_chain = create_stuff_documents_chain(llm,qa_pr,document_variable_name="context")


    # 3. Final Zinciri multi_retriever ile güncelliyoruz
    full_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    response=full_chain.invoke({"input":"Ambulans ve acil bakım teknikerleri hangi görevlere sahiptir?"})
    print("Bulunan belgeler:")
    for doc in response["context"]:
        print(f"Kaynak :{doc.metadata.get('source')} | İçerik özeti : {doc.page_content[:100]}...")
    print("\n LLM cevabı:" ,response["answer"])

retrieval_chain()