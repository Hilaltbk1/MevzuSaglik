from sqlalchemy.orm import Session

from models import SessionModel, LogModel
from models.query_model import QueryRequest
from  models.message_model import  MessageModel
#create -read-update-delete
#sqlalchemy ıle olusturdugum modeller

#----------------------CREATE İŞLEMLERİ----------------------------------
#MESSAGE -create
def create_message(db: Session,current_session_id:int,content :str,sender_type:str):
    new_message=MessageModel(
        session_id=current_session_id,
        sender_type=sender_type,
        content=content,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

#SESSİON-craete
def create_session(db: Session, user_name: str):
    new_session=SessionModel(
        user_name=user_name,
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
#----------------------READ İŞLEMLERİ---------------------------
#READ MESSAGE
def read_message(db: Session, current_session_id: int):
    return db.query(MessageModel).filter_by(session_id=current_session_id).order_by(MessageModel.created_at.asc()).all()

#READ-SESSİON
def read_session(db: Session, session_name: str):
    return db.query(SessionModel).filter_by(user_name=session_name).first()

#READ-LOG
def read_log(db: Session, message_id: int):
    return db.query(LogModel).filter_by(message_id=message_id).all()




