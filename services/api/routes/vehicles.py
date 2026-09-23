from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db import get_db
from models import Driver, Position, Vehicle

router = APIRouter()


@router.get("/vehicles")
def list_vehicles(tenant_id: str = Query(...), db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.tenant_id == tenant_id).all()

    out = []
    for v in vehicles:
        driver = db.query(Driver).filter(Driver.id == v.driver_id).first()
        latest = (
            db.query(Position)
            .filter(Position.vehicle_id == v.id)
            .order_by(Position.ts.desc())
            .first()
        )
        out.append(
            {
                "id": str(v.id),
                "reg_number": v.reg_number,
                "route_name": v.route_name,
                "driver_name": driver.name if driver else None,
                "last_position": (
                    {"lat": latest.lat, "lon": latest.lon, "speed_kmh": latest.speed_kmh, "ts": latest.ts}
                    if latest
                    else None
                ),
            }
        )
    return out


@router.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        return {"error": "not found"}
    driver = db.query(Driver).filter(Driver.id == v.driver_id).first()
    return {
        "id": str(v.id),
        "tenant_id": str(v.tenant_id),
        "reg_number": v.reg_number,
        "route_name": v.route_name,
        "driver": {"id": str(driver.id), "name": driver.name} if driver else None,
    }
