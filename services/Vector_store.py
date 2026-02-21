from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
from pathlib import Path  # <--- Eksik olan kahraman bu!
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import VectorParams,Distance
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

from utils import llm_client


load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
# try-except
#vector store olusturma
#default olarak false
def initialize_vector_store(rebuild_db=False):
    from preprocessing.preprocessing import file_path, flatten_mevzuat_object
    print("1. Fonksiyon başladı...")

    chunks = None
    vector_store = None
    try:
        # --- 1. JSON Okuma ve Parçalama ---
        print(f"2. Dosya yolu okunuyor: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"3. JSON yüklendi, {len(data)} adet kayıt bulundu.")
            #list print(type(data))

        doc_list = []
        BASE_DIR = Path(__file__).resolve().parent.parent
        PROCESSED_DATA_PATH =BASE_DIR / "data" / "Json" / "islenmis_mevzuat_verileri.json"
        # --- KRİTİK EKLEME: LLM KONTROLÜ ---

        try:
            if os.path.exists(PROCESSED_DATA_PATH) and not rebuild_db:
                print(f"✅ {PROCESSED_DATA_PATH} bulundu! LLM'e sormadan dosyadan yükleniyor...")
                with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
                    saved_docs = json.load(f)
                # Kayıtlı verileri tekrar Document nesnelerine çeviriyoruz
                doc_list = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in saved_docs]
            else:
                print("🔍 Veriler baştan işleniyor (LLM çalışacak)...")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    for d in data:
                        duzlesmis_metin = flatten_mevzuat_object(d, llm_client)
                        doc_list.append(Document(
                            page_content=duzlesmis_metin,
                            metadata={"Mevzuat_Adi": d.get("Mevzuat Adı", ""), "Mevzuat_Türü": d.get("Mevzuat Türü", "")}
                        ))

                # İŞLEM BİTTİĞİ AN KAYDET: Bir daha hata alırsan burayı atlasın
                json_data = [{"page_content": d.page_content, "metadata": d.metadata} for d in doc_list]
                with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                print(f"💾 İşlenmiş veriler yedeklendi: {PROCESSED_DATA_PATH}")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500, chunk_overlap=150, length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

            chunks = text_splitter.split_documents(doc_list)
            print(f"4. Chunking tamamlandı. Toplam parça sayısı: {len(chunks)}")


            embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",model_kwargs={'device': 'cpu'},encode_kwargs={'normalize_embeddings': False})

            #vector store
            QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
            client = QdrantClient(host=QDRANT_HOST, port=6333, timeout=300,prefer_grpc=False)
            COLLECTION_NAME = "mevzu_saglik_docs"

            #  Varsa Bağlan, Yoksa Kur
            exists = client.collection_exists(COLLECTION_NAME)


            #  Varsa ve SİLMEK istiyorsak SİL
            if exists and not rebuild_db:
                print("✅ Mevcut koleksiyona bağlanıldı.")
                return QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding), chunks
            #  Yoksa veya Silindiyse OLUŞTUR ve YÜKLE

            if exists: client.delete_collection(COLLECTION_NAME)
            vector_size = len(embedding.embed_query("test"))
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

            vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)

            print(f"🚀 {len(chunks)} parça yükleniyor (Lütfen bekleyin)...")
            vector_store.add_documents(documents=chunks, batch_size=100)
            print("✅ Yükleme başarıyla tamamlandı.")

            return vector_store, chunks

        except Exception as e:

            print("\n" + "=" * 50)

            print("❌ KRİTİK HATA: Vektör veritabanı kurulurken bir sorun oluştu!")

            print(f"Hata Detayı: {repr(e)}")

            print("=" * 50 + "\n")

            raise e
    except Exception as e:
            print(e)

initialize_vector_store(rebuild_db=False)
