from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from preprocessing.preprocessing import file_path, flatten_mevzuat_object,format_table_as_text
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import VectorParams,Distance
from qdrant_client import QdrantClient

# try-except
try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON içeriği liste değil")

    #text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    doc_list=[]

    for d in data:

        #her mevzuatın düz metin hali
        duzlesmis_metin = flatten_mevzuat_object(d)

        #Chunking İşlemi RecursiveCharacterSplit
        doc_list.append(Document(
                page_content=duzlesmis_metin,
            metadata={
                "Mevzuat_Adi": d.get("Mevzuat Adı", ""),
                "Mevzuat_Turu": d.get("Mevzuat Türü", ""),


            }
            )
        )
    #text_documents
    chunks=text_splitter.split_documents(doc_list)

     #embedding model
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2",model_kwargs={'device': 'cuda'},encode_kwargs={"batch_size": 32})
    vector_size = len(embedding.embed_query("test"))


    client=QdrantClient(host="localhost",port=6333,timeout=60)
    client.delete_collection("mevzuat")

    COLLECTION_NAME="mevzuat"
    try:
        if not client.collection_exists(COLLECTION_NAME):
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
                )
            )
        vector_store=QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=embedding
             )

        vector_store.add_documents(documents=chunks,batch_size=100)

        print(vector_store)
    finally:
        client.close()


except FileNotFoundError:
    print("❌ JSON dosyası bulunamadı")

except SystemExit:
    pass

except Exception as e:
    print("❌ Gerçek hata:", repr(e))
