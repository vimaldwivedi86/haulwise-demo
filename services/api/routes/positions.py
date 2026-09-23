from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from deps import require_tenant_id
from models import Position, Vehicle

router = APIRouter()


@router.get("/vehicles/{vehicle_id}/positions")
def position_history(
    vehicle_id: str,
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(require_tenant_id),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle or str(vehicle.tenant_id) != tenant_id:
        raise HTTPException(status_code=404, detail="vehicle not found")

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
