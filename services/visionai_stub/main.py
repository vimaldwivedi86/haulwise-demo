"""Fictional third-party AI vendor. Stores whatever it receives on its own
volume so a later DELETE is real and visible, not just a status code."""

import json
import pathlib
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="visionai_stub")

STORE_DIR = pathlib.Path("/data/subjects")
STORE_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/v1/face/verify")
async def verify(request: Request):
    body = await request.json()
    subject_id = body.get("subject_id") or body.get("name") or "unknown"
    safe_id = str(subject_id).replace("/", "_")

    record = {
        **body,
        "received_at": time.time(),
    }
    (STORE_DIR / f"{safe_id}.json").write_text(json.dumps(record, indent=2))

    return {
        "subject_id": subject_id,
        "match": True,
        "confidence": 0.97,
        "stored": True,
    }


@app.delete("/v1/subjects/{subject_id}")
async def delete_subject(subject_id: str):
    safe_id = subject_id.replace("/", "_")
    f = STORE_DIR / f"{safe_id}.json"
    existed = f.exists()
    if existed:
        f.unlink()
    return {"subject_id": subject_id, "deleted": existed, "ack_id": f"ack-{int(time.time()*1000)}"}


@app.get("/v1/subjects/{subject_id}")
async def get_subject(subject_id: str):
    safe_id = subject_id.replace("/", "_")
    f = STORE_DIR / f"{safe_id}.json"
    if not f.exists():
        return JSONResponse(status_code=404, content={"subject_id": subject_id, "found": False})
    return json.loads(f.read_text())


@app.get("/v1/subjects")
async def list_subjects():
    return {
        "subjects": [p.stem for p in STORE_DIR.glob("*.json")],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
