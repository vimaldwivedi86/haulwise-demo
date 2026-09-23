from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import Tenant

router = APIRouter()


@router.get("/tenants")
def list_tenants(db: Session = Depends(get_db)):
    rows = db.query(Tenant).order_by(Tenant.name).all()
    return [{"id": str(t.id), "name": t.name} for t in rows]
