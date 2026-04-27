from __future__ import annotations
import re
import secrets
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.schemas.user_model import UserModel
from backend.schemas.tenant_model import PlanType
from backend.database import crud
from passlib.context import CryptContext

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Kimlik Dogrulama"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PASSWORD_RE = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$')


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def get_password_hash(password):
    return pwd_context.hash(password)


def validate_password(password: str):
    if not PASSWORD_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="Parola en az 8 karakter, 1 büyük harf, 1 rakam ve 1 özel karakter içermelidir."
        )


def send_reset_email(to_email: str, token: str):
    import os
    
    # Resend API key'i .env'den oku
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    
    print(f"🔍 Resend Debug - API Key: {resend_api_key[:10] if resend_api_key else 'YOK'}...")
    print(f"🔍 Resend Debug - From: {from_email}")

    # Resend kullan
    if resend_api_key:
        try:
            import requests
            
            body = (
                f"Merhaba,\n\n"
                f"Şifre sıfırlama talebiniz alındı.\n\n"
                f"Aşağıdaki kodu 'Şifremi Unuttum' bölümüne girin:\n\n"
                f"  {token}\n\n"
                f"Bu kod 30 dakika geçerlidir.\n\n"
                f"MevzuSaglik Ekibi"
            )
            
            headers = {
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "from": from_email,
                "to": [to_email],
                "subject": "MevzuSaglik - Şifre Sıfırlama",
                "text": body
            }
            
            response = requests.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=data
            )
            
            print(f"✅ Resend yanıtı: {response.status_code}")
            print(f"📧 Resend detay: {response.json()}")
            
            if response.status_code == 200:
                print(f"✅ E-posta gönderildi (Resend): {to_email}")
                return True
            else:
                print(f"⚠️  Resend hatası: {response.json()}")
                return False
                
        except Exception as e:
            print(f"⚠️  Resend hatası: {e}")
            return False
    
    print("⚠️  RESEND_API_KEY bulunamadı")
    return False


# ── REGISTER ──────────────────────────────────────────────
@router.post("/register")
@limiter.limit("5/minute")
async def register_user(request: Request, db: Session = Depends(get_db)):
    body      = await request.json()
    user_name = body.get("user_name", "").strip()
    password  = body.get("password", "")
    email     = body.get("email", "").strip() or None

    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Kullanıcı adı ve parola zorunludur.")

    validate_password(password)

    if db.query(UserModel).filter(UserModel.username == user_name).first():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış.")

    if email and db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")

    new_tenant = crud.create_tenant(db, name=user_name, plan=PlanType.free, api_key=secrets.token_hex(32))
    new_user   = UserModel(
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
        "message":      "Kayıt başarılı",
        "user_name":    new_user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id":    new_tenant.id,
        "api_key":      new_tenant.api_key,
    }


# ── LOGIN ──────────────────────────────────────────────────
@router.post("/login")
@limiter.limit("10/minute")
async def login_user(request: Request, db: Session = Depends(get_db)):
    body      = await request.json()
    user_name = body.get("user_name", "").strip()
    password  = body.get("password", "")

    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Kullanıcı adı ve parola zorunludur.")

    user = db.query(UserModel).filter(UserModel.username == user_name).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya parola.")

    from backend.schemas.tenant_model import TenantModel
    tenant      = db.query(TenantModel).filter_by(id=user.tenant_id).first()
    new_session = crud.create_session(db, user_name, user.tenant_id)
    return {
        "message":      "Giriş başarılı",
        "user_name":    user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id":    user.tenant_id,
        "api_key":      tenant.api_key if tenant else "",
    }


# ── FORGOT PASSWORD ────────────────────────────────────────
@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, db: Session = Depends(get_db)):
    try:
        body  = await request.json()
        email = body.get("email", "").strip()
        if not email:
            raise HTTPException(status_code=400, detail="E-posta adresi zorunludur.")

        user = db.query(UserModel).filter(UserModel.email == email).first()
        if user:
            token                    = secrets.token_hex(6).upper()
            user.reset_token         = token
            user.reset_token_expires = datetime.now() + timedelta(minutes=30)
            db.commit()
            
            # E-posta göndermeyi dene, başarısız olursa hata verme
            email_sent = send_reset_email(email, token)
            if not email_sent:
                print(f"⚠️  E-posta gönderilemedi ama işlem devam ediyor: {email}")

        return {"message": "E-posta kayıtlıysa sıfırlama kodu gönderildi."}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️  Forgot password hatası: {e}")
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


# ── RESET PASSWORD ─────────────────────────────────────────
@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    body         = await request.json()
    email        = body.get("email", "").strip()
    token        = body.get("token", "").strip().upper()
    new_password = body.get("new_password", "")

    if not email or not token or not new_password:
        raise HTTPException(status_code=400, detail="E-posta, kod ve yeni parola zorunludur.")

    validate_password(new_password)

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user or user.reset_token != token:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş kod.")

    if user.reset_token_expires < datetime.now():
        raise HTTPException(status_code=400, detail="Kodun süresi dolmuş. Lütfen tekrar talep edin.")

    user.password_hash       = get_password_hash(new_password)
    user.reset_token         = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Parola başarıyla güncellendi."}
