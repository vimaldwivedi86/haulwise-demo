import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from eta import eta_minutes
from models import Position, ShareLink, Vehicle

router = APIRouter()

LINK_LIFETIME = timedelta(hours=24)


@router.post("/vehicles/{vehicle_id}/share")
def create_share_link(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")

    token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + LINK_LIFETIME
    link = ShareLink(token=token, vehicle_id=vehicle.id, tenant_id=vehicle.tenant_id, expires_at=expires_at)
    db.add(link)
    db.commit()

    return {"token": link.token, "url": f"/t/{link.token}", "expires_at": expires_at}


@router.get("/t/{token}")
def resolve_share_link(token: str, db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="link expired")

    vehicle = db.query(Vehicle).filter(Vehicle.id == link.vehicle_id).first()
    latest = (
        db.query(Position)
        .filter(Position.vehicle_id == link.vehicle_id)
        .order_by(Position.ts.desc())
        .first()
    )

    eta = None
    if latest and vehicle:
        eta = eta_minutes(vehicle.route_name, latest.lat, latest.lon, latest.speed_kmh)

    return {
        "reg_number": vehicle.reg_number if vehicle else None,
        "position": {"lat": latest.lat, "lon": latest.lon, "ts": latest.ts} if latest else None,
        "eta_minutes": eta,
    }
