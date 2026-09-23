from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import storage
from db import get_db
from models import Driver, VideoEvent

router = APIRouter()


@router.get("/video_events")
def list_video_events(tenant_id: str = Query(...), limit: int = Query(50, le=500), db: Session = Depends(get_db)):
    rows = (
        db.query(VideoEvent)
        .filter(VideoEvent.tenant_id == tenant_id)
        .order_by(VideoEvent.ts.desc())
        .limit(limit)
        .all()
    )
    out = []
    for e in rows:
        driver = db.query(Driver).filter(Driver.id == e.driver_id).first() if e.driver_id else None
        out.append(
            {
                "id": str(e.id),
                "vehicle_id": str(e.vehicle_id),
                "driver_name": driver.name if driver else None,
                "type": e.type,
                "severity": e.severity,
                "clip_url": storage.object_url(e.clip_key) if e.clip_key else None,
                "face_snapshot_url": storage.object_url(e.face_snapshot_key) if e.face_snapshot_key else None,
                "ts": e.ts,
            }
        )
    return out
