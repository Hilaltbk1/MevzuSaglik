from dotenv import load_dotenv

# Bu üçü LangChain ana paketinden gelmeli
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever

# Bunlar genellikle core veya community paketindedir, LangChain üzerinden de erişilebilir
from langchain.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_ollama import ChatOllama

from config.configuration import Settings
from prompt.My_Prompt import create_prompt
from services.Vector_store import initialize_vector_store

settings=Settings()
# Satır 2 civarındaki hata için:
def retrieval_chain():
    load_dotenv()

    llm = ChatOllama(
        model="llama3.1:8b",
        temperature=0,
        base_url="http://host.docker.internal:11434"
    )
    #vector_store,chunks
    v_db,split_text=initialize_vector_store()

    #vector search
    vector_retrievers=v_db.as_retriever(search_type="similarity",search_kwargs={"k": 3})
    # BM25
    bm25_retrievers=BM25Retriever.from_documents(split_text)
    #mix
    mix_retrievers=EnsembleRetriever(retrievers=[vector_retrievers,bm25_retrievers],weights=[0.5,0.5])

    # 5. Final Retrieval Chain

    qa_pr,c_pr = create_prompt()

    history_aware_retriever=create_history_aware_retriever(
        llm,
        mix_retrievers,
        c_pr
    )


    #okuma ve cevaplama -llm ı beslemek
    question_answer_chain = create_stuff_documents_chain(llm,qa_pr,document_variable_name="context")


    # 3. Final Zinciri multi_retriever ile güncelliyoruz
    full_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # BU KISIM ÖNEMLİ: session.py'nin 'chain.full_chain' olarak erişebilmesi için
    # fonksiyonun bu nesneyi döndürmesi gerekir.
    class ChainContainer:
        def __init__(self, fc):
            self.full_chain = fc

    return ChainContainer(full_chain)

