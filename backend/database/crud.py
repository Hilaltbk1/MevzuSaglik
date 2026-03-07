from __future__ import annotations

import os
import uuid
from typing import List
import io
from fastapi import UploadFile
from google.generativeai import embedding
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from backend.preprocessing.preprocessing import flatten_mevzuat_object
from backend.schemas import SessionModel, LogModel
from backend.schemas.message_model import  MessageModel

# Embedding modelini bir kez oluştur


async def upload_files(files :List[UploadFile]):
    from backend.utils import llm_client
    embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    doc_list=[]
    for file in files:
        content=await file.read()
        pdf_file=io.BytesIO(content)

        processed_data=flatten_mevzuat_object(pdf_file,llm_client)

        doc_list.append(Document(
            page_content=str(processed_data),
            metadata={"Mevzuat_Adi": processed_data.get("Mevzuat Adı", ""), "Mevzuat_Türü": processed_data.get("Mevzuat Türü", "")}
        ))


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=150, length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(doc_list)

    QDRANT_HOST = os.getenv("QDRANT_HOST")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    client = QdrantClient(
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            prefer_grpc=False,
            timeout=300
        )
    COLLECTION_NAME = "mevzu_saglik_docs"

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embedding  # 'embedding' objesinin dışarıda tanımlı olduğundan emin ol
    )

    if chunks:
        vector_store.add_documents(documents=chunks)
        print(f"✅ {len(chunks)} parça Qdrant'a başarıyla eklendi.")

    return {"message": f"{len(files)} dosya işlendi ve {len(chunks)} parça kaydedildi."}



#----------------------CREATE İŞLEMLERİ----------------------------------
#MESSAGE -create
def create_message(db: Session, session_id: int, content: str, sender_type: str):
    new_message = MessageModel(
        session_id=session_id,
        sender_type=sender_type,
        content=content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

#SESSİON-craete
def create_session(db: Session, user_name: str):
    new_session=SessionModel(
        user_name=user_name,
        session_uuid=str(uuid.uuid4()),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

#LOG-create
def create_log(db:Session,status_code:int,request_data:str,response_data:str,error_message:str,message_id:int):
    new_log=LogModel(
        status_code=status_code,
        request=request_data,
        response=response_data,
        error_message=error_message,
        message_id=message_id,
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log
#----------------------İSTENENİLEN KULLANICIYA GÖRE READ İŞLEMLERİ---------------------------

#sessiona ait tüm mesajları mesaj tablosu  uuid ile bulma
def get_session_by_uuid(db: Session, session_uuid: str):
    return db.query(SessionModel).filter(SessionModel.session_uuid == session_uuid).first()



def get_messages_by_uuid(db: Session, session_uuid: str):
    return db.query(MessageModel).join(SessionModel).filter(SessionModel.session_uuid == session_uuid).order_by(MessageModel.created_at.asc()).all()

#---------------------TÜM READ İŞLEMLERİ--------------------
#istenilen session id ye göre listelio
def read_messages_by_session(db: Session, session_id: int):
    """Sadece seçilen oturuma ait mesajları tarihe göre sıralı getirir."""
    return db.query(MessageModel).filter_by(session_id=session_id).order_by(MessageModel.created_at.asc()).all()

#READ-LOG
# idye gore istenilen mesajin logu
def read_log(db: Session, message_id: int):
    return db.query(LogModel).filter_by(message_id=message_id).all()

#tüm sessionsları listeler
def read_user_sessions(db: Session, user_name: str):
    # Kullanıcının tüm oturumlarını, en yeniden eskiye doğru getirir
    return db.query(SessionModel).filter(SessionModel.user_name == user_name).order_by(SessionModel.created_at.desc()).all()


def read_all_messages(db:Session):
    return db.query(MessageModel).all()

def read_all_sessions(db:Session):
    return db.query(SessionModel).all()

def read_all_logs(db:Session):
    return db.query(LogModel).all()















