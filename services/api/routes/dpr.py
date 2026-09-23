from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from models import DprRequest, DprStep

router = APIRouter()


@router.get("/dpr")
def list_dpr(driver_id: str = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.query(DprRequest)
        .filter(DprRequest.driver_id == driver_id)
        .order_by(DprRequest.opened_at.desc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "cmp_request_id": r.cmp_request_id,
            "trigger": r.trigger,
            "status": r.status,
            "opened_at": r.opened_at,
            "closed_at": r.closed_at,
        }
        for r in rows
    ]


@router.get("/dpr/{dpr_id}")
def get_dpr(dpr_id: str, db: Session = Depends(get_db)):
    dpr = db.query(DprRequest).filter(DprRequest.id == dpr_id).first()
    if not dpr:
        raise HTTPException(status_code=404, detail="not found")

    steps = db.query(DprStep).filter(DprStep.dpr_id == dpr.id).order_by(DprStep.step).all()

    return {
        "id": str(dpr.id),
        "cmp_request_id": dpr.cmp_request_id,
        "driver_id": str(dpr.driver_id),
        "trigger": dpr.trigger,
        "status": dpr.status,
        "opened_at": dpr.opened_at,
        "closed_at": dpr.closed_at,
        "steps": [
            {
                "step": s.step,
                "name": s.name,
                "status": s.status,
                "evidence": s.evidence,
                "ts": s.ts,
            }
            for s in steps
        ],
    }
