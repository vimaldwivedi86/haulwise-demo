import json
import os
import time

import paho.mqtt.client as mqtt

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ["MQTT_PORT"])


def connect() -> mqtt.Client:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    for _ in range(30):
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            return client
        except (ConnectionRefusedError, OSError):
            time.sleep(2)
    raise RuntimeError("could not reach mosquitto")


def publish_gps(client: mqtt.Client, payload: dict):
    client.publish(f"haulwise/gps/{payload['vehicle_id']}", json.dumps(payload))


def publish_dashcam(client: mqtt.Client, payload: dict):
    client.publish(f"haulwise/dashcam/{payload['vehicle_id']}", json.dumps(payload))
