from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Driver, Position, ShareLink, Vehicle

router = APIRouter()


@router.post("/vehicles/{vehicle_id}/share")
def create_share_link(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="vehicle not found")

    link = ShareLink(token="", vehicle_id=vehicle.id, tenant_id=vehicle.tenant_id)
    db.add(link)
    db.flush()
    link.token = str(link.id)
    db.commit()

    return {"token": link.token, "url": f"/t/{link.token}"}


@router.get("/t/{token}")
def resolve_share_link(token: str, db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")

    vehicle = db.query(Vehicle).filter(Vehicle.id == link.vehicle_id).first()
    driver = db.query(Driver).filter(Driver.id == vehicle.driver_id).first() if vehicle else None
    latest = (
        db.query(Position)
        .filter(Position.vehicle_id == link.vehicle_id)
        .order_by(Position.ts.desc())
        .first()
    )

    return {
        "reg_number": vehicle.reg_number if vehicle else None,
        "driver_name": driver.name if driver else None,
        "driver_phone": driver.phone if driver else None,
        "position": {"lat": latest.lat, "lon": latest.lon, "ts": latest.ts} if latest else None,
    }
