from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import scrutora_client
from db import get_db
from models import Driver

router = APIRouter()


@router.get("/drivers/{driver_id}/scrutora-state")
def scrutora_consent_state(driver_id: str, db: Session = Depends(get_db)):
    """Proxies Scrutora's consent state query so the browser never sees the
    API key. Looks the subject up by the driver's phone number."""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="not found")

    try:
        return scrutora_client.get_consent_state(driver.phone, "phone")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"scrutora state query failed: {exc}")
