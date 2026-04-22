from __future__ import annotations
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import VectorParams, Distance
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from backend.logger import logger

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "false"
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
if langchain_api_key:
    os.environ["LANGCHAIN_API_KEY"] = langchain_api_key


def initialize_vector_store(rebuild_db=False):
    from backend.preprocessing.preprocessing import file_path, flatten_mevzuat_object
    from backend.llm_client import llm_client
    logger.info("Vector store başlatılıyor...")

    chunks = None
    vector_store = None
    try:
        logger.info(f"Dosya yolu okunuyor: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"JSON yüklendi, {len(data)} adet kayıt bulundu.")

        doc_list = []
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "Json", "islenmis_mevzuat_verileri.json")

        if os.path.exists(PROCESSED_DATA_PATH):
            logger.info("Yedek bulundu, LLM atlanıyor...")
            with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
                saved_docs = json.load(f)
            doc_list = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in saved_docs]
        else:
            logger.info("Yedek bulunamadı, veriler baştan işleniyor...")
            for d in data:
                duzlesmis_metin = flatten_mevzuat_object(d, llm_client)
                doc_list.append(Document(
                    page_content=duzlesmis_metin,
                    metadata={"Mevzuat_Adi": d.get("Mevzuat Adı", ""), "Mevzuat_Türü": d.get("Mevzuat Türü", "")}
                ))
            json_data = [{"page_content": d.page_content, "metadata": d.metadata} for d in doc_list]
            with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            logger.info(f"İşlenmiş veriler yedeklendi: {PROCESSED_DATA_PATH}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=200, length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(doc_list)
        logger.info(f"Chunking tamamlandı. Toplam parça: {len(chunks)}")

        embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            output_dimensionality=3072
        )

        QDRANT_HOST    = os.getenv("QDRANT_HOST", "").strip().strip('\n').strip('\r')
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip().strip('\n').strip('\r')
        client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY, prefer_grpc=False, timeout=300)
        COLLECTION_NAME = "mevzu_saglik_docs"
        exists = client.collection_exists(COLLECTION_NAME)

        if rebuild_db or not exists:
            if exists:
                logger.info(f"Eski koleksiyon siliniyor: {COLLECTION_NAME}")
                client.delete_collection(COLLECTION_NAME)

            logger.info("Yeni koleksiyon oluşturuluyor...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
            )
            vector_store  = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)
            total_chunks  = len(chunks)

            for i in range(0, total_chunks, 50):
                batch = chunks[i:i + 50]
                vector_store.add_documents(documents=batch)
                logger.info(f"İlerleme: {min(i+50, total_chunks)}/{total_chunks}")

            logger.info("Yükleme tamamlandı.")
        else:
            logger.info("Mevcut koleksiyona bağlanıldı.")
            vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)

        return vector_store, chunks
    except Exception as e:
        logger.error(f"Vector store hatası: {e}")
        return None, None