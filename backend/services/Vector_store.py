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



load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")


def initialize_vector_store(rebuild_db=False):
    from backend.preprocessing.preprocessing import file_path, flatten_mevzuat_object
    from backend.llm_client import llm_client
    print("1. Fonksiyon başladı...")

    chunks = None
    vector_store = None
    try:

        print(f"2. Dosya yolu okunuyor: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"3. JSON yüklendi, {len(data)} adet kayıt bulundu.")

        doc_list = []


        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "Json", "islenmis_mevzuat_verileri.json")

        if os.path.exists(PROCESSED_DATA_PATH):
            print(f"✅ Yedek bulundu! LLM'i atlayıp Qdrant işlemlerine geçiyorum...")
            with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
                saved_docs = json.load(f)
            doc_list = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in saved_docs]
        else:
            print("🔍 Yedek bulunamadı, veriler baştan işleniyor (LLM çalışacak)...")
            for d in data:
                duzlesmis_metin = flatten_mevzuat_object(d, llm_client)
                doc_list.append(Document(
                    page_content=duzlesmis_metin,
                    metadata={"Mevzuat_Adi": d.get("Mevzuat Adı", ""), "Mevzuat_Türü": d.get("Mevzuat Türü", "")}
                ))


            json_data = [{"page_content": d.page_content, "metadata": d.metadata} for d in doc_list]
            with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            print(f"💾 İşlenmiş veriler yedeklendi: {PROCESSED_DATA_PATH}")


        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=200, length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(doc_list)
        print(f"4. Chunking tamamlandı. Toplam parça sayısı: {len(chunks)}")

        embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            output_dimensionality=3072
        )


        QDRANT_HOST = os.getenv("QDRANT_HOST")
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
        client = QdrantClient(
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            prefer_grpc=False,
            timeout=300
        )
        COLLECTION_NAME = "mevzu_saglik_docs"

        exists = client.collection_exists(COLLECTION_NAME)


        if rebuild_db or not exists:
            if exists:
                print(f"🗑️ Eski hatalı koleksiyon siliniyor: {COLLECTION_NAME}")
                client.delete_collection(COLLECTION_NAME)

            print(f"🏗️ Yeni koleksiyon oluşturuluyor (Boyut: 3072)...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
            )

            vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)

            batch_size = 50
            total_chunks = len(chunks)
            print(f"🚀 Toplam {total_chunks} parça Qdrant'a yükleniyor...")

            for i in range(0, total_chunks, batch_size):
                batch = chunks[i: i + batch_size]
                vector_store.add_documents(documents=batch)
                current_count = min(i + batch_size, total_chunks)
                print(f"⏳ İlerleme: {current_count}/{total_chunks} parça yüklendi...")

            print("✅ Yükleme başarıyla tamamlandı.")
        else:
            print("✅ Mevcut koleksiyona bağlanıldı.")
            vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embedding)

        return vector_store, chunks
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        return None, None

if __name__ == "__main__":
    # Veritabanını sıfırdan oluşturmak için rebuild_db=True yapıyoruz
    print("🚀 Veritabanı güncelleniyor (800 chunk size)...")
    v_db, ch = initialize_vector_store(rebuild_db=True)
    if v_db:
        print("✅ Veritabanı başarıyla güncellendi ve yeni koleksiyon oluşturuldu.")
    else:
        print("❌ Güncelleme başarısız.")