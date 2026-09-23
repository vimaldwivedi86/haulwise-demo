from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db import get_db
from models import Position

router = APIRouter()


@router.get("/vehicles/{vehicle_id}/positions")
def position_history(vehicle_id: str, limit: int = Query(200, le=2000), db: Session = Depends(get_db)):
    rows = (
        db.query(Position)
        .filter(Position.vehicle_id == vehicle_id)
        .order_by(Position.ts.desc())
        .limit(limit)
        .all()
    )
    return [
        {"lat": r.lat, "lon": r.lon, "speed_kmh": r.speed_kmh, "heading": r.heading, "ts": r.ts}
        for r in rows
    ]
