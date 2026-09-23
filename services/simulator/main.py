import os
import random
import time

from sqlalchemy import create_engine, text

from clips import ensure_clips
from mqtt_client import connect, publish_dashcam, publish_gps
from routes import RoutePlayer, load_routes

DATABASE_URL = os.environ["DATABASE_URL"]
TICK_SECONDS = 2.0
EVENT_TYPES = ["harsh_braking", "lane_departure", "drowsiness", "face_mismatch"]
EVENT_SEVERITY = {"harsh_braking": "medium", "lane_departure": "medium", "drowsiness": "high", "face_mismatch": "high"}


def wait_for_db():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    for _ in range(60):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception:
            time.sleep(2)
    raise RuntimeError("database never became ready")


def load_fleet(engine):
    routes = load_routes()
    label_to_waypoints = {r["label"]: r["waypoints"] for r in routes.values()}

    # The api container runs migrations and seeds the fleet on its own
    # startup, which can still be in flight when this container starts, so
    # retry until the vehicles table exists and has rows rather than
    # depending on service start order.
    vehicles = []
    for _ in range(60):
        try:
            with engine.connect() as conn:
                vehicles = conn.execute(
                    text("SELECT id, tenant_id, driver_id, reg_number, route_name FROM vehicles")
                ).mappings().all()
            if vehicles:
                break
        except Exception:
            pass
        time.sleep(2)

    fleet = []
    for i, v in enumerate(vehicles):
        waypoints = label_to_waypoints.get(v["route_name"])
        if not waypoints:
            continue
        player = RoutePlayer(waypoints, speed_kmh=random.uniform(55, 75), offset=(i * 0.13) % 1.0)
        fleet.append({"vehicle": v, "player": player})
    return fleet


def main():
    engine = wait_for_db()
    fleet = load_fleet(engine)
    print(f"simulator: {len(fleet)} vehicles loaded")

    try:
        ensure_clips()
    except Exception as exc:
        print(f"simulator: clip generation skipped ({exc})")

    client = connect()
    client.loop_start()

    while True:
        for entry in fleet:
            entry["player"].advance(TICK_SECONDS)
            lat, lon, heading = entry["player"].position()
            v = entry["vehicle"]
            publish_gps(
                client,
                {
                    "vehicle_id": str(v["id"]),
                    "tenant_id": str(v["tenant_id"]),
                    "lat": lat,
                    "lon": lon,
                    "speed_kmh": round(entry["player"].speed_kmh, 1),
                    "heading": round(heading, 1),
                },
            )

            if random.random() < 0.02:
                etype = random.choice(EVENT_TYPES)
                publish_dashcam(
                    client,
                    {
                        "vehicle_id": str(v["id"]),
                        "driver_id": str(v["driver_id"]) if v["driver_id"] else None,
                        "tenant_id": str(v["tenant_id"]),
                        "type": etype,
                        "severity": EVENT_SEVERITY[etype],
                        "clip_key": f"clips/{etype}.mp4",
                        "face_snapshot_key": f"faces/{v['driver_id']}.svg" if etype == "face_mismatch" and v["driver_id"] else None,
                    },
                )

        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
