from __future__ import annotations
import re
import secrets
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.schemas.user_model import UserModel
from backend.schemas.tenant_model import PlanType
from backend.database import crud
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["Kimlik Dogrulama"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Şifre kuralı: min 8 karakter, 1 büyük harf, 1 rakam, 1 özel karakter
PASSWORD_RE = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$')


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def get_password_hash(password):
    return pwd_context.hash(password)


def validate_password(password: str):
    if not PASSWORD_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="Parola en az 8 karakter, 1 büyük harf, 1 rakam ve 1 özel karakter (!@#$ vb.) içermelidir."
        )


def send_reset_email(to_email: str, token: str):
    """SMTP ile şifre sıfırlama e-postası gönderir."""
    smtp_host   = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port   = int(os.getenv("SMTP_PORT", "587"))
    smtp_user   = os.getenv("SMTP_USER", "")
    smtp_pass   = os.getenv("SMTP_PASS", "")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

    reset_link = f"{frontend_url}/?reset_token={token}"
    body = (
        f"Merhaba,\n\n"
        f"Şifre sıfırlama talebiniz alındı.\n\n"
        f"Aşağıdaki kodu giriş ekranındaki 'Şifremi Unuttum' bölümüne girin:\n\n"
        f"  {token}\n\n"
        f"Bu kod 30 dakika geçerlidir.\n\n"
        f"Eğer bu talebi siz yapmadıysanız bu e-postayı görmezden gelin.\n\n"
        f"MevzuSaglik Ekibi"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "MevzuSaglik - Şifre Sıfırlama"
    msg["From"]    = smtp_user
    msg["To"]      = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
    except Exception as e:
        print(f"E-posta gönderilemedi: {e}")
        raise HTTPException(status_code=500, detail="E-posta gönderilemedi. SMTP ayarlarını kontrol edin.")


# ── REGISTER ──────────────────────────────────────────────
@router.post("/register")
def register_user(request: dict, db: Session = Depends(get_db)):
    user_name = request.get("user_name", "").strip()
    password  = request.get("password", "")
    email     = request.get("email", "").strip() or None

    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Kullanici adi ve parola zorunludur.")

    validate_password(password)

    if db.query(UserModel).filter(UserModel.username == user_name).first():
        raise HTTPException(status_code=400, detail="Bu kullanici adi zaten alinmis.")

    if email and db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayitli.")

    new_tenant = crud.create_tenant(db, name=user_name, plan=PlanType.free, api_key=secrets.token_hex(32))

    new_user = UserModel(
        username=user_name,
        email=email,
        password_hash=get_password_hash(password),
        tenant_id=new_tenant.id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_session = crud.create_session(db, user_name, new_tenant.id)
    return {
        "message": "Kayit basarili",
        "user_name": new_user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id": new_tenant.id,
        "api_key": new_tenant.api_key,
    }


# ── LOGIN ──────────────────────────────────────────────────
@router.post("/login")
def login_user(request: dict, db: Session = Depends(get_db)):
    user_name = request.get("user_name", "").strip()
    password  = request.get("password", "")

    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Kullanici adi ve parola zorunludur.")

    user = db.query(UserModel).filter(UserModel.username == user_name).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Gecersiz kullanici adi veya parola.")

    from backend.schemas.tenant_model import TenantModel
    tenant = db.query(TenantModel).filter_by(id=user.tenant_id).first()
    new_session = crud.create_session(db, user_name, user.tenant_id)
    return {
        "message": "Giris basarili",
        "user_name": user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id": user.tenant_id,
        "api_key": tenant.api_key if tenant else "",
    }


# ── FORGOT PASSWORD ────────────────────────────────────────
@router.post("/forgot-password")
def forgot_password(request: dict, db: Session = Depends(get_db)):
    email = request.get("email", "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="E-posta adresi zorunludur.")

    user = db.query(UserModel).filter(UserModel.email == email).first()
    # Güvenlik: kullanıcı bulunamasa da aynı mesajı döndür
    if user:
        token = secrets.token_hex(6).upper()  # 6 bayt = 12 karakter hex kodu
        user.reset_token         = token
        user.reset_token_expires = datetime.now() + timedelta(minutes=30)
        db.commit()
        send_reset_email(email, token)

    return {"message": "Eğer bu e-posta kayıtlıysa sıfırlama kodu gönderildi."}


# ── RESET PASSWORD ─────────────────────────────────────────
@router.post("/reset-password")
def reset_password(request: dict, db: Session = Depends(get_db)):
    email        = request.get("email", "").strip()
    token        = request.get("token", "").strip().upper()
    new_password = request.get("new_password", "")

    if not email or not token or not new_password:
        raise HTTPException(status_code=400, detail="E-posta, kod ve yeni parola zorunludur.")

    validate_password(new_password)

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user or user.reset_token != token:
        raise HTTPException(status_code=400, detail="Gecersiz veya suresi dolmus kod.")

    if user.reset_token_expires < datetime.now():
        raise HTTPException(status_code=400, detail="Kodun suresi dolmus. Lutfen tekrar talep edin.")

    user.password_hash        = get_password_hash(new_password)
    user.reset_token          = None
    user.reset_token_expires  = None
    db.commit()

    return {"message": "Parola basariyla guncellendi."}
