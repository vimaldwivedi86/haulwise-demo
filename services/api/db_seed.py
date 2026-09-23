"""Synthetic seed data only: Faker en_IN, generated phone numbers, no real
faces. See CLAUDE.md rule 3."""

import json
import pathlib
import random

from faker import Faker
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Driver, Tenant, Vehicle

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

ROUTES_FILE = pathlib.Path(__file__).parent / "db" / "seed" / "routes.json"

TENANTS_AND_ROUTES = [
    ("Aravalli Cement", "NH48"),
    ("Konkan Foods", "MUMBAI_PUNE_EXPRESSWAY"),
]

VEHICLES_PER_TENANT = 3

STATE_CODES = ["RJ", "MH", "DL", "HR", "GJ", "PB"]


def run(db: Session):
    if db.query(Tenant).count() > 0:
        print("seed: tenants already present, skipping")
        return

    routes = json.loads(ROUTES_FILE.read_text())

    for tenant_name, route_key in TENANTS_AND_ROUTES:
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()

        for i in range(VEHICLES_PER_TENANT):
            driver = Driver(
                tenant_id=tenant.id,
                name=fake.name(),
                phone=fake.msisdn()[-10:],
                dl_number=f"{random.choice(STATE_CODES)}-{fake.random_int(1000000000, 9999999999)}",
                face_image_key=None,
                face_embedding=None,
            )
            db.add(driver)
            db.flush()

            vehicle = Vehicle(
                tenant_id=tenant.id,
                driver_id=driver.id,
                reg_number=f"{random.choice(STATE_CODES)}{fake.random_int(10,99)}{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}{fake.random_int(1000,9999)}",
                route_name=routes[route_key]["label"],
            )
            db.add(vehicle)

    db.commit()
    print("seed: done")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        run(db)
    finally:
        db.close()
