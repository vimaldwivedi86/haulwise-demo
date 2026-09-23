import hashlib
import hmac
import json
import os
import threading

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from db import SessionLocal
from dpr.orchestrator import run as run_dpr_workflow
from models import Consent, Driver, DprRequest

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

        dpr_id = None
        if event == "consent.withdrawn" and purpose == "face_verification":
            cmp_dpr_id = body["cmp_dpr_id"]
            dpr = DprRequest(
                cmp_request_id=cmp_dpr_id,
                driver_id=driver.id,
                trigger=f"consent.withdrawn:{purpose}",
            )
            db.add(dpr)
            db.commit()
            dpr_id = str(dpr.id)
            threading.Thread(target=run_dpr_workflow, args=(dpr_id,), daemon=True).start()

        return {"received": True, "dpr_id": dpr_id}
    finally:
        db.close()
