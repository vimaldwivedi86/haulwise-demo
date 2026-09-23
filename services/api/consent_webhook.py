import hashlib
import hmac
import json
import os

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Consent, Driver

router = APIRouter()

WEBHOOK_SECRET = os.environ.get("CMP_WEBHOOK_SECRET", "haulwise-demo-shared-secret")


def _verify_signature(raw_body: bytes, signature: str | None):
    if not signature:
        raise HTTPException(status_code=401, detail="missing signature")
    expected = hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="invalid signature")


@router.post("/webhooks/consent")
async def consent_webhook(request: Request, x_cmp_signature: str | None = Header(default=None)):
    raw = await request.body()
    _verify_signature(raw, x_cmp_signature)
    body = json.loads(raw)

    event = body["event"]
    driver_id = body["driver_id"]
    purpose = body["purpose"]
    receipt_id = body.get("receipt_id")

    db: Session = SessionLocal()
    try:
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="unknown driver_id")

        status = "granted" if event == "consent.granted" else "withdrawn"
        db.add(Consent(driver_id=driver.id, purpose=purpose, status=status, receipt_id=receipt_id))
        db.commit()

        return {"received": True}
    finally:
        db.close()
