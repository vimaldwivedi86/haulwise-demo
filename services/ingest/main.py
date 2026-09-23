import json
import os
import time
import uuid

import paho.mqtt.client as mqtt
import redis
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
REDIS_URL = os.environ["REDIS_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
r = redis.from_url(REDIS_URL, decode_responses=True)


def handle_gps(payload: dict):
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO positions (vehicle_id, tenant_id, lat, lon, speed_kmh, heading) "
                "VALUES (:vehicle_id, :tenant_id, :lat, :lon, :speed_kmh, :heading)"
            ),
            payload,
        )
    r.publish("positions", json.dumps(payload, default=str))


def handle_dashcam(payload: dict):
    event_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO video_events (id, vehicle_id, driver_id, tenant_id, type, severity, clip_key, face_snapshot_key) "
                "VALUES (:id, :vehicle_id, :driver_id, :tenant_id, :type, :severity, :clip_key, :face_snapshot_key)"
            ),
            {**payload, "id": event_id},
        )
    r.publish(
        "video_events",
        json.dumps({"id": event_id, "event_type": payload["type"], **payload}, default=str),
    )


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    if msg.topic.startswith("haulwise/gps/"):
        handle_gps(payload)
    elif msg.topic.startswith("haulwise/dashcam/"):
        handle_dashcam(payload)


def main():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    for attempt in range(30):
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            break
        except (ConnectionRefusedError, OSError):
            time.sleep(2)

    client.subscribe("haulwise/gps/#")
    client.subscribe("haulwise/dashcam/#")
    print("ingest: listening on haulwise/gps/# and haulwise/dashcam/#")
    client.loop_forever()


if __name__ == "__main__":
    main()
