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
    """
    Vector store'u başlatır.
    - rebuild_db=True: Collection'ı sıfırdan oluşturur ve JSON'dan yükler
    - rebuild_db=False: Mevcut collection'a bağlanır, yoksa boş oluşturur
    """
    from backend.preprocessing.preprocessing import file_path, flatten_mevzuat_object
    from backend.llm_client import llm_client
    logger.info("Vector store başlatılıyor...")

    chunks = None
    vector_store = None
    try:
        embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            output_dimensionality=3072
        )

        QDRANT_HOST    = os.getenv("QDRANT_HOST", "").strip().strip('\n').strip('\r')
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip().strip('\n').strip('\r')
        client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY, prefer_grpc=False, timeout=300)
        COLLECTION_NAME = "mevzu_saglik_docs"  # Qdrant'taki gerçek collection adı
        exists = client.collection_exists(COLLECTION_NAME)

        if rebuild_db:
            # REBUILD MODE: Collection'ı sıfırdan oluştur ve JSON'dan yükle
            logger.warning("⚠️  REBUILD_DB=True: Collection sıfırdan oluşturulacak!")
            
            if exists:
                logger.info(f"Eski koleksiyon siliniyor: {COLLECTION_NAME}")
                client.delete_collection(COLLECTION_NAME)

            logger.info("Yeni koleksiyon oluşturuluyor...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
            )
            
            # JSON dosyasından veri yükle
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
            
            vector_store  = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)
            total_chunks  = len(chunks)

            for i in range(0, total_chunks, 50):
                batch = chunks[i:i + 50]
                vector_store.add_documents(documents=batch)
                logger.info(f"İlerleme: {min(i+50, total_chunks)}/{total_chunks}")

            logger.info("✅ JSON verilerinden yükleme tamamlandı.")
            
        elif not exists:
            # Collection yok, boş oluştur
            logger.warning(f"⚠️  Collection '{COLLECTION_NAME}' bulunamadı!")
            logger.info("📦 Boş collection oluşturuluyor...")
            try:
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
                )
                logger.info(f"✅ Boş collection '{COLLECTION_NAME}' oluşturuldu.")
                logger.info("💡 PDF yükleyerek veri ekleyebilirsiniz.")
                vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)
            except Exception as create_error:
                logger.error(f"❌ Collection oluşturma hatası: {create_error}")
                raise ValueError(f"Collection oluşturulamadı: {create_error}")
            
        else:
            # Collection mevcut, bağlan
            logger.info(f"✅ Mevcut collection '{COLLECTION_NAME}' kullanılıyor.")
            vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)
            
            # Chunks'ları Qdrant'tan çek (BM25 için gerekli)
            try:
                logger.info("📦 Mevcut dokümanlar Qdrant'tan alınıyor...")
                scroll_result, _ = client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=10000,
                    with_payload=True,
                )
                
                # Point'leri Document'lere dönüştür
                from langchain_core.documents import Document
                chunks = []
                for point in scroll_result:
                    if point.payload:
                        page_content = point.payload.get("page_content", "")
                        metadata = point.payload.get("metadata", {})
                        if page_content:
                            chunks.append(Document(page_content=page_content, metadata=metadata))
                
                logger.info(f"✅ {len(chunks)} chunk Qdrant'tan yüklendi (BM25 için)")
            except Exception as e:
                logger.error(f"⚠️ Chunks yüklenemedi, BM25 devre dışı kalacak: {e}")
                chunks = []

        return vector_store, chunks
    except Exception as e:
        logger.error(f"❌ Vector store hatası: {e}")
        logger.error(f"❌ Hata tipi: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None, None
