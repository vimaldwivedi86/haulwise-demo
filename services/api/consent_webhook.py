"""Receives webhooks from the real Scrutora CMP (see scrutora_client.py for
what's confirmed vs assumed about this API). Scrutora sends the subject's
full current purpose state on every change, not a single purpose+action
pair, so this diffs the incoming state against the last row Haulwise has on
file for each purpose to work out what actually changed."""

import hashlib
import hmac
import json
import os
import threading
import uuid

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

import face
from db import SessionLocal
from dpr.orchestrator import run as run_dpr_workflow
from models import Consent, Driver, DprRequest

router = APIRouter()

WEBHOOK_SECRET = os.environ.get("SCRUTORA_WEBHOOK_SECRET", "")
SIGNATURE_PREFIX = "sha256="


def _verify_signature(raw_body: bytes, signature: str | None):
    if not signature or not signature.startswith(SIGNATURE_PREFIX):
        raise HTTPException(status_code=401, detail="missing or malformed X-Scrutora-Signature-256")
    provided = signature[len(SIGNATURE_PREFIX):]
    expected = hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=401, detail="invalid signature")


def _resolve_driver(db: Session, data: dict) -> Driver:
    """The docs don't show a concrete example of the identifying fields in
    a webhook's `data` object, only that /state takes identifier +
    identifier_type (email or phone). Tries the field names that would
    match Haulwise's own identifier_type=phone convention, and fails loudly
    -- not silently -- if none match, so a real payload's actual shape
    surfaces immediately instead of being guessed at."""
    phone = data.get("phone") or (data.get("identifier") if data.get("identifier_type") == "phone" else None)
    if phone:
        driver = db.query(Driver).filter(Driver.phone == phone).first()
        if driver:
            return driver

    email = data.get("email") or (data.get("identifier") if data.get("identifier_type") == "email" else None)
    if email:
        raise HTTPException(
            status_code=501,
            detail=f"webhook identified the subject by email ({email}), but drivers only carry phone numbers in this demo",
        )

    raise HTTPException(
        status_code=400,
        detail=f"could not resolve a driver from webhook data; got keys {list(data.keys())}",
    )


@router.post("/webhooks/consent")
async def consent_webhook(
    request: Request,
    x_scrutora_signature_256: str | None = Header(default=None),
):
    raw = await request.body()
    _verify_signature(raw, x_scrutora_signature_256)
    body = json.loads(raw)

    event = body["event"]
    data = body.get("data", {})
    purposes: dict = data.get("purposes", {})

    if event == "dsr.created":
        # A formal rights request (access/correction/erasure/withdraw/
        # grievance/nominate), identified by the requester's email rather
        # than a driver's phone, and gated on Scrutora's own email
        # verification before it's actioned. Haulwise doesn't need its own
        # copy of this queue -- it already lives under Records & requests
        # in the Scrutora dashboard -- so this just acknowledges receipt.
        return {"received": True, "event": event}

    db: Session = SessionLocal()
    try:
        driver = _resolve_driver(db, data)

        changed = []
        for purpose, granted in purposes.items():
            latest = (
                db.query(Consent)
                .filter(Consent.driver_id == driver.id, Consent.purpose == purpose)
                .order_by(Consent.ts.desc())
                .first()
            )
            new_status = "granted" if granted else "withdrawn"
            if latest and latest.status == new_status:
                continue
            db.add(Consent(driver_id=driver.id, purpose=purpose, status=new_status, receipt_id=None))
            changed.append((purpose, new_status))
        db.commit()

        # Mirrors a real onboarding/verification call now that consent is
        # on record, instead of waiting on a client-side button click.
        if ("face_verification", "granted") in changed:
            face.onboard_driver(db, driver)

        dpr_id = None
        if ("face_verification", "withdrawn") in changed:
            # The docs don't show a request/DPR id on this webhook shape --
            # that only appears in a DSR creation response, which this
            # lighter-weight banner-driven withdrawal may not go through.
            # Generate a local reference rather than pretend one arrived.
            dpr = DprRequest(
                cmp_request_id=f"local-{uuid.uuid4().hex[:10]}",
                driver_id=driver.id,
                trigger="consent.withdrawn:face_verification",
            )
            db.add(dpr)
            db.commit()
            dpr_id = str(dpr.id)
            threading.Thread(target=run_dpr_workflow, args=(dpr_id,), daemon=True).start()

        return {"received": True, "event": event, "changed": changed, "dpr_id": dpr_id}
    finally:
        db.close()
