"""`make burst` - fires a quick batch of face_mismatch dashcam events for
every driver in the fleet, so the demo operator can immediately see whether
withdrawn consent stopped the vendor call."""

import os
import time

from sqlalchemy import create_engine, text

from mqtt_client import connect, publish_dashcam

DATABASE_URL = os.environ["DATABASE_URL"]


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        vehicles = conn.execute(
            text("SELECT id, tenant_id, driver_id FROM vehicles WHERE driver_id IS NOT NULL")
        ).mappings().all()

    client = connect()
    client.loop_start()

    for v in vehicles:
        publish_dashcam(
            client,
            {
                "vehicle_id": str(v["id"]),
                "driver_id": str(v["driver_id"]),
                "tenant_id": str(v["tenant_id"]),
                "type": "face_mismatch",
                "severity": "high",
                "clip_key": "clips/face_mismatch.mp4",
                "face_snapshot_key": f"faces/{v['driver_id']}.svg",
            },
        )
        print(f"burst: face_mismatch fired for driver {v['driver_id']}")
        time.sleep(0.5)

    time.sleep(1)
    client.loop_stop()


if __name__ == "__main__":
    main()
