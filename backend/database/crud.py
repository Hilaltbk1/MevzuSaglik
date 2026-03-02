import uuid
from sqlalchemy.orm import Session
from backend.schemas import SessionModel, LogModel
from backend.schemas.message_model import  MessageModel

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






















