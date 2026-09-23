import os

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db import get_db
from models import Driver, VendorCall

router = APIRouter()

VISIONAI_URL = os.environ["VISIONAI_URL"]


@router.get("/vendor/calls")
def list_vendor_calls(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.query(VendorCall).order_by(VendorCall.ts.desc()).limit(limit).all()
    out = []
    for c in rows:
        driver = db.query(Driver).filter(Driver.id == c.driver_id).first() if c.driver_id else None
        out.append(
            {
                "id": c.id,
                "vendor": c.vendor,
                "endpoint": c.endpoint,
                "method": c.method,
                "payload_preview": c.payload_preview,
                "driver_id": str(c.driver_id) if c.driver_id else None,
                "driver_name": driver.name if driver else None,
                "ts": c.ts,
            }
        )
    return out


@router.get("/vendor/holdings")
def vendor_holdings(db: Session = Depends(get_db)):
    try:
        with httpx.Client(timeout=5, verify=False) as client:
            resp = client.get(f"{VISIONAI_URL}/v1/subjects")
            subject_ids = resp.json().get("subjects", [])
    except httpx.HTTPError:
        return {"subjects": [], "error": "vendor unreachable"}

    drivers = {str(d.id): d.name for d in db.query(Driver).all()}
    out = []
    for sid in subject_ids:
        out.append({"subject_id": sid, "matched_driver_name": drivers.get(sid)})
    return {"subjects": out}
