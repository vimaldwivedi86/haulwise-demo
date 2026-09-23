from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import face
from db import get_db
from models import Consent, Driver

router = APIRouter()


@router.get("/drivers")
def list_drivers(tenant_id: str = Query(...), db: Session = Depends(get_db)):
    rows = db.query(Driver).filter(Driver.tenant_id == tenant_id).all()
    return [{"id": str(d.id), "name": d.name, "phone": d.phone} for d in rows]


@router.get("/drivers/{driver_id}")
def get_driver(driver_id: str, db: Session = Depends(get_db)):
    d = db.query(Driver).filter(Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": str(d.id), "name": d.name, "phone": d.phone, "tenant_id": str(d.tenant_id)}


@router.get("/drivers/{driver_id}/consents")
def driver_consents(driver_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(Consent)
        .filter(Consent.driver_id == driver_id)
        .order_by(Consent.ts.asc())
        .all()
    )
    latest_by_purpose: dict[str, Consent] = {}
    for c in rows:
        latest_by_purpose[c.purpose] = c

    return {
        purpose: {"status": c.status, "receipt_id": c.receipt_id, "ts": c.ts}
        for purpose, c in latest_by_purpose.items()
    }


@router.post("/drivers/{driver_id}/onboard")
def onboard(driver_id: str, db: Session = Depends(get_db)):
    d = db.query(Driver).filter(Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="not found")
    face.onboard_driver(db, d)
    return {"onboarded": True, "face_image_key": d.face_image_key}
