import asyncio
import json
import os

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import consent_webhook
import face
from db import SessionLocal
from models import Driver, VideoEvent
from routes import consent_state, dpr, drivers, positions, share, tenants, vehicles, vendor_log, video_events

app = FastAPI(title="Haulwise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants.router)
app.include_router(vehicles.router)
app.include_router(positions.router)
app.include_router(share.router)
app.include_router(drivers.router)
app.include_router(consent_state.router)
app.include_router(video_events.router)
app.include_router(vendor_log.router)
app.include_router(dpr.router)
app.include_router(consent_webhook.router)

REDIS_URL = os.environ["REDIS_URL"]

_ws_clients: set[WebSocket] = set()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/positions")
async def ws_positions(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_clients.discard(ws)


async def _broadcast(message: dict):
    dead = []
    for client in _ws_clients:
        try:
            await client.send_json(message)
        except Exception:
            dead.append(client)
    for d in dead:
        _ws_clients.discard(d)


def _handle_face_mismatch(event_id: str):
    db = SessionLocal()
    try:
        event = db.query(VideoEvent).filter(VideoEvent.id == event_id).first()
        if not event or not event.driver_id:
            return
        driver = db.query(Driver).filter(Driver.id == event.driver_id).first()
        if not driver:
            return
        face.call_vendor_verify(db, driver, event_id=str(event.id))
    finally:
        db.close()


async def _redis_listener():
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("positions", "video_events")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        channel = message["channel"]
        data = json.loads(message["data"])

        if channel == "positions":
            await _broadcast({"type": "position", **data})
        elif channel == "video_events":
            await _broadcast({"type": "video_event", **data})
            if data.get("event_type") == "face_mismatch":
                await asyncio.get_event_loop().run_in_executor(
                    None, _handle_face_mismatch, data["id"]
                )


_background_tasks: set[asyncio.Task] = set()


@app.on_event("startup")
async def startup():
    # asyncio only holds a weak reference to a task created this way, so a
    # strong reference has to be kept somewhere or the task (and the redis
    # subscription it holds open) gets garbage collected almost immediately.
    task = asyncio.create_task(_redis_listener())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
