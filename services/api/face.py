import os

import httpx
from sqlalchemy.orm import Session

import storage
from avatar import svg_avatar
from models import Consent, Driver, VendorCall

VISIONAI_URL = os.environ["VISIONAI_URL"]


def has_active_consent(db: Session, driver: Driver, purpose: str) -> bool:
    latest = (
        db.query(Consent)
        .filter(Consent.driver_id == driver.id, Consent.purpose == purpose)
        .order_by(Consent.ts.desc())
        .first()
    )
    return latest is not None and latest.status == "granted"


def onboard_driver(db: Session, driver: Driver):
    image_key = f"faces/{driver.id}.svg"
    storage.put_bytes(image_key, svg_avatar(driver.name), content_type="image/svg+xml")
    driver.face_image_key = image_key
    driver.face_embedding = f"embedding-{driver.id}"
    db.add(driver)
    db.commit()

    call_vendor_verify(db, driver)


def call_vendor_verify(db: Session, driver: Driver, event_id: str | None = None):
    if not has_active_consent(db, driver, "face_verification"):
        db.add(
            VendorCall(
                vendor="visionai_stub",
                endpoint="/v1/face/verify",
                method="BLOCKED",
                payload_preview={"reason": "face_verification consent not granted", "subject_id": f"drv-{driver.id}"},
                driver_id=driver.id,
            )
        )
        db.commit()
        return

    # Pseudonymous subject_id only -- name, phone and DL number never leave
    # Haulwise. The vendor is declared in config/processors.yaml.
    payload = {
        "subject_id": f"drv-{driver.id}",
        "embedding_ref": driver.face_embedding,
        "event_id": event_id,
    }

    # verify=False only because visionai_stub's TLS cert is self-signed for
    # this demo; a real deployment would trust a real CA and drop this.
    with httpx.Client(timeout=10, verify=False) as client:
        client.post(f"{VISIONAI_URL}/v1/face/verify", json=payload)

    db.add(
        VendorCall(
            vendor="visionai_stub",
            endpoint="/v1/face/verify",
            method="POST",
            payload_preview=payload,
            driver_id=driver.id,
        )
    )
    db.commit()
