import stripe
import os
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from backend.database.db_setup import get_db
from backend.schemas.tenant_model import TenantModel, PlanType

router = APIRouter(prefix="/billing", tags=["Faturalama"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()

PLAN_PRICE_IDS = {
    "pro":        "price_1TBEDZCy8ysSERSo2askuLJo".strip(),
    "enterprise": "price_1TBEL2Cy8ysSERSoBPUXm1ns".strip(),
}


from backend.dependencies.auth import get_current_tenant

@router.post("/checkout")
def create_checkout(tenant_id: int, plan: PlanType, db: Session = Depends(get_db), tenant=Depends(get_current_tenant)):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe yapilandirilmamis.")

    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok.")

    if plan not in PLAN_PRICE_IDS:
        raise HTTPException(status_code=400, detail=f"Gecersiz plan: {plan}")

    tenant = db.query(TenantModel).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant bulunamadi: {tenant_id}")

    BASE_URL = os.getenv("BACKEND_URL", "https://mevzusaglik.com.tr").strip()
    # Eğer Hugging Face URL'i ise, Cloudflare domain'ini kullan
    if "hf.space" in BASE_URL:
        BASE_URL = "https://mevzusaglik.com.tr"
    
    plan_price_id = PLAN_PRICE_IDS[plan].strip()

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": plan_price_id, "quantity": 1}],
            metadata={"tenant_id": str(tenant_id), "plan": plan},

            success_url=f"{BASE_URL}/?payment=success&plan={plan.value}&tenant_id={tenant_id}",
            cancel_url=f"{BASE_URL}/?payment=cancel",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Stripe hatasi: {str(e)}")

    # Planı hemen DB'ye yaz (webhook gecikmesine karşı)
    tenant.plan = plan
    db.commit()

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
            payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET", "")
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook dogrulamasi basarisiz")

    if event["type"] == "checkout.session.completed":
        meta = event["data"]["object"]["metadata"]
        tenant = db.query(TenantModel).filter_by(id=int(meta["tenant_id"])).first()
        if tenant:
            tenant.plan = meta["plan"]
            db.commit()

    return {"ok": True}