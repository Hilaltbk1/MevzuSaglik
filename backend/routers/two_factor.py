from __future__ import annotations
import base64
import hashlib
import io
from datetime import datetime
import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.database.db_setup import get_db
from backend.dependencies.auth import get_current_user
from backend.schemas.login_session import LoginSessionModel
from backend.schemas.user_model import UserModel
from backend.utils.jwt_utils import create_access_token

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth/2fa", tags=["2FA"])

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()

@router.post("/setup")
@limiter.limit("5/minute")
def setup_2fa(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """TOTP secret üretir, QR kodu base64 PNG olarak döndürür. Henüz aktif değil."""
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA zaten etkin. Önce kaldırın.")

    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    db.commit()

    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email or current_user.username,
        issuer_name="MevzuSaglik",
    )
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return {"secret": secret, "qr_base64": qr_base64,
            "note": "QR'ı Google Authenticator vb. ile okutun, ardından /auth/2fa/verify çağırın"}

@router.post("/verify")
@limiter.limit("5/minute")
async  def verify_2fa(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """İlk kurulumda girilen 6 haneli kodu doğrular, 2FA'yı açar, kurtarma kodlarını verir."""
    body = await request.json()
    code = (body.get("code") or "").strip()
    if not code or not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Kod zorunludur.")

    if not pyotp.TOTP(current_user.totp_secret).verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Kod geçersiz.")

    current_user.is_2fa_enabled = True

    # 10 tek kullanımlık kurtarma kodu — hash'li saklanır, düz metin BİR KEZ gösterilir
    import secrets as _secrets
    codes = [_secrets.token_hex(5).upper() for _ in range(10)]
    current_user.recovery_codes = ",".join(_hash_code(c) for c in codes)
    db.commit()

    return {"message": "2FA etkinleştirildi", "recovery_codes": codes,
            "note": "Bu kodları güvenli bir yerde saklayın. Tekrar gösterilmeyecekler."}

@router.post("/login")
@limiter.limit("10/minute")
async def login_2fa(request: Request, db: Session = Depends(get_db)):
    """Şifre doğru olan ama 2FA açık kullanıcıya token verir (kod veya kurtarma kodu)."""
    body = await request.json()
    user_name = (body.get("user_name") or "").strip()
    code = (body.get("code") or "").strip()

    user = db.query(UserModel).filter(UserModel.username == user_name).first()
    if not user or not user.is_2fa_enabled or not user.totp_secret:
        raise HTTPException(status_code=401, detail="2FA doğrulaması açılamadı.")

    ok = pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)

    # Kurtarma kodu denemesi
    used_recovery = False
    if not ok and user.recovery_codes:
        hashes = [h.strip() for h in user.recovery_codes.split(",")]
        h = _hash_code(code)
        if h in hashes:
            hashes.remove(h)
            user.recovery_codes = ",".join(hashes) if hashes else None
            used_recovery = True
            ok = True

    if not ok:
        raise HTTPException(status_code=401, detail="Geçersiz doğrulama kodu.")

    db.commit()  # kullanılan kurtarma kodunu düşür

    login_session = LoginSessionModel(
        user_id=user.id,
        expires_at=datetime.now() + __import__("datetime").timedelta(hours=8),
        revoked=False,
    )
    db.add(login_session)
    db.commit()
    db.refresh(login_session)
    access_token = create_access_token({"sid": str(login_session.id)})

    from backend.schemas.tenant_model import TenantModel
    tenant = db.query(TenantModel).filter_by(id=user.tenant_id).first()
    from backend.database import crud
    new_session = crud.create_session(db, user.username, user.tenant_id, user.id)

    return {
        "message": "Giriş başarılı",
        "user_name": user.username,
        "session_uuid": new_session.session_uuid,
        "tenant_id": user.tenant_id,
        "api_key": tenant.api_key if tenant else "",
        "access_token": access_token,
        "token_type": "bearer",
        "recovery_code_used": used_recovery,
    }