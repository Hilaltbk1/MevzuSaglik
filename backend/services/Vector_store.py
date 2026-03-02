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
    print("1. Fonksiyon başladı...")

    chunks = None
    vector_store = None
    try:
        # --- 1. JSON Okuma ---
        print(f"2. Dosya yolu okunuyor: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"3. JSON yüklendi, {len(data)} adet kayıt bulundu.")

        doc_list = []

        # --- DÜZELTİLEN YER: Kesin Dosya Yolu ---
        # Hatalı olanı bununla değiştir:
        PROCESSED_DATA_PATH = r"/backend/data/Json/islenmis_mevzuat_verileri.json"
        # --- DÜZELTİLEN YER: LLM KONTROL MANTIĞI ---
        # Artık rebuild_db=True olsa bile eğer yedek dosya varsa LLM'i çalıştırmaz, dosyadan okur.
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

            # İşlem bittiğinde kaydet
            json_data = [{"page_content": d.page_content, "metadata": d.metadata} for d in doc_list]
            with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            print(f"💾 İşlenmiş veriler yedeklendi: {PROCESSED_DATA_PATH}")

        # --- 2. Chunking ---
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=150, length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(doc_list)
        print(f"4. Chunking tamamlandı. Toplam parça sayısı: {len(chunks)}")

        embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

        # --- 3. Qdrant Bağlantısı ---
        QDRANT_HOST = os.getenv("QDRANT_HOST")  # Örn: https://xxxx.qdrant.io
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
        # Bulut bağlantısı için url ve api_key parametrelerini kullanıyoruz
        client = QdrantClient(
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            timeout=300
        )
        COLLECTION_NAME = "mevzu_saglik_docs"

        exists = client.collection_exists(COLLECTION_NAME)

        # Eğer rebuild_db True ise veya koleksiyon yoksa: SİL ve 3072 boyutunda YENİDEN KUR
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
        print("\n" + "=" * 50)
        print(f"❌ KRİTİK HATA: {repr(e)}")
        print("=" * 50 + "\n")
        raise e



if __name__ == "__main__":
    # Import'u sadece dosya çalışınca, fonksiyon içinde yapıyoruz (Döngü kırıldı!)
    try:
        from backend.utils import llm_client

        print("✅ Bağımlılıklar yüklendi, veritabanı işlemi başlıyor...")
        initialize_vector_store(rebuild_db=True)
    except Exception as e:
        print(f"❌ Çalıştırma hatası: {e}")