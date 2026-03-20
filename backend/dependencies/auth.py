from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.schemas.user_model import UserModel
from backend.schemas.tenant_model import PlanType
from backend.database import crud
from passlib.context import CryptContext

router = APIRouter(
    prefix="/auth",
    tags=["Kimlik Doğrulama"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


@router.post("/register")
def register_user(request: dict, db: Session = Depends(get_db)):
    user_name = request.get("user_name")
    password = request.get("password")

    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Kullanıcı adı ve parola zorunludur.")

    existing_user = db.query(UserModel).filter(UserModel.username == user_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış.")

    new_tenant = crud.create_tenant(db, name=user_name, plan=PlanType.free, api_key=f"sk_{user_name}_demo")

    hashed_password = get_password_hash(password)
    new_user = UserModel(
        username=user_name,
        password_hash=hashed_password,
        tenant_id=new_tenant.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_session = crud.create_session(db, user_name, new_tenant.id)

    return {
        "message": "Kayıt başarılı",
        "user_name": new_user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id": new_tenant.id,
    }


@router.post("/login")
def login_user(request: dict, db: Session = Depends(get_db)):
    user_name = request.get("user_name")
    password = request.get("password")

    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Kullanıcı adı ve parola zorunludur.")

    user = db.query(UserModel).filter(UserModel.username == user_name).first()
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya parola.")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya parola.")

    new_session = crud.create_session(db, user_name, user.tenant_id)

    return {
        "message": "Giriş başarılı",
        "user_name": user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id": user.tenant_id,
    }