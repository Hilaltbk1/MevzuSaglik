# backend/routers/billing.py
import stripe, os
from fastapi import APIRouter, Request, HTTPException, Depends, Header  # ← çift HTTPException kaldırıldı
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.schemas.tenant_model import TenantModel, PlanType

router = APIRouter(prefix="/billing", tags=["Faturalama"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PLAN_PRICE_IDS = {
    "pro":"price_1TBEDZCy8ysSERSo2askuLJo ",   # ← prod_ değil price_ olmalı (aşağıda açıkladım)
    "enterprise":"price_1TBEL2Cy8ysSERSoBPUXm1ns",
}

@router.post("/checkout")
def create_checkout(tenant_id: int, plan: PlanType, db: Session = Depends(get_db)):
    BASE_URL = os.getenv("BACKEND_URL", "https://mevzusaglik.onrender.com")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": PLAN_PRICE_IDS[plan], "quantity": 1}],
        metadata={"tenant_id": str(tenant_id), "plan": plan},
        success_url=f"{BASE_URL}/success",
        cancel_url=f"{BASE_URL}/cancel",
    )
    return {"checkout_url": session.url}

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(...),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook doğrulaması başarısız")

    if event["type"] == "checkout.session.completed":
        meta   = event["data"]["object"]["metadata"]
        tenant = db.query(TenantModel).filter_by(id=int(meta["tenant_id"])).first()
        if tenant:
            tenant.plan = meta["plan"]
            db.commit()

    return {"ok": True}