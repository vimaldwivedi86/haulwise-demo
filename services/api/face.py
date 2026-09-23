import os

import httpx
from sqlalchemy.orm import Session

import storage
from avatar import svg_avatar
from models import Driver, VendorCall

VISIONAI_URL = os.environ["VISIONAI_URL"]


def onboard_driver(db: Session, driver: Driver):
    image_key = f"faces/{driver.id}.svg"
    storage.put_bytes(image_key, svg_avatar(driver.name), content_type="image/svg+xml")
    driver.face_image_key = image_key
    driver.face_embedding = f"embedding-{driver.id}"
    db.add(driver)
    db.commit()

    call_vendor_verify(db, driver)


def call_vendor_verify(db: Session, driver: Driver, event_id: str | None = None):
    payload = {
        "name": driver.name,
        "phone": driver.phone,
        "dl_number": driver.dl_number,
        "image_key": driver.face_image_key,
        "image_url": storage.object_url(driver.face_image_key) if driver.face_image_key else None,
        "event_id": event_id,
    }

    with httpx.Client(timeout=10) as client:
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
