"""Stands in for the real Scrutora CMP in this demo build. No credentials or
API surface for the actual product were available, so this small service
plays the CMP's role end to end: purpose-level consent capture, a hash
chained receipt log, DPR request creation on withdrawal, an outbound signed
webhook to Haulwise, and an endpoint Haulwise posts DPR step status back to.
Swap this for the real Scrutora CMP integration before the actual demo."""

import hashlib
import hmac
import json
import os
import pathlib
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="cmp_stub")

DATA_DIR = pathlib.Path("/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_FILE = DATA_DIR / "receipts.json"
DPR_FILE = DATA_DIR / "dpr.json"

HAULWISE_API_URL = os.environ.get("HAULWISE_API_URL", "http://api:8000")
WEBHOOK_SECRET = os.environ.get("CMP_WEBHOOK_SECRET", "haulwise-demo-shared-secret")


def _load(path: pathlib.Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save(path: pathlib.Path, data: dict):
    path.write_text(json.dumps(data, indent=2, default=str))


def _sign(body: bytes) -> str:
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


class ConsentAction(BaseModel):
    driver_id: str
    purpose: str


class DprStatusUpdate(BaseModel):
    status: str
    detail: str | None = None


def _append_receipt(driver_id: str, purpose: str, action: str) -> dict:
    receipts = _load(RECEIPTS_FILE)
    chain = receipts.setdefault(driver_id, [])
    prev_hash = chain[-1]["hash"] if chain else "genesis"
    seq = len(chain) + 1
    ts = time.time()
    payload = f"{prev_hash}|{seq}|{purpose}|{action}|{ts}"
    receipt_hash = hashlib.sha256(payload.encode()).hexdigest()
    receipt = {
        "receipt_id": f"rcpt-{driver_id[:8]}-{seq:04d}",
        "seq": seq,
        "purpose": purpose,
        "action": action,
        "ts": ts,
        "prev_hash": prev_hash,
        "hash": receipt_hash,
    }
    chain.append(receipt)
    _save(RECEIPTS_FILE, receipts)
    return receipt


async def _send_webhook(event_type: str, payload: dict):
    body = {"event": event_type, **payload}
    raw = json.dumps(body).encode()
    signature = _sign(raw)
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{HAULWISE_API_URL}/webhooks/consent",
            content=raw,
            headers={
                "Content-Type": "application/json",
                "X-Cmp-Signature": signature,
            },
        )


@app.post("/consent/grant")
async def grant(action: ConsentAction):
    receipt = _append_receipt(action.driver_id, action.purpose, "granted")
    await _send_webhook(
        "consent.granted",
        {"driver_id": action.driver_id, "purpose": action.purpose, "receipt_id": receipt["receipt_id"]},
    )
    return receipt


@app.post("/consent/withdraw")
async def withdraw(action: ConsentAction):
    receipt = _append_receipt(action.driver_id, action.purpose, "withdrawn")

    dpr_id = f"dpr-{uuid.uuid4().hex[:10]}"
    dpr_store = _load(DPR_FILE)
    dpr_store[dpr_id] = {
        "dpr_id": dpr_id,
        "driver_id": action.driver_id,
        "purpose": action.purpose,
        "status": "raised",
        "opened_at": time.time(),
        "closed_at": None,
        "history": [],
    }
    _save(DPR_FILE, dpr_store)

    await _send_webhook(
        "consent.withdrawn",
        {
            "driver_id": action.driver_id,
            "purpose": action.purpose,
            "receipt_id": receipt["receipt_id"],
            "cmp_dpr_id": dpr_id,
        },
    )
    return {"receipt": receipt, "cmp_dpr_id": dpr_id}


@app.get("/receipts/{driver_id}")
async def receipts(driver_id: str):
    return _load(RECEIPTS_FILE).get(driver_id, [])


@app.post("/dpr/{cmp_request_id}/status")
async def post_status(cmp_request_id: str, update: DprStatusUpdate):
    dpr_store = _load(DPR_FILE)
    record = dpr_store.get(cmp_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="unknown cmp_request_id")

    record["status"] = update.status
    record["history"].append({"status": update.status, "detail": update.detail, "ts": time.time()})
    if update.status == "closed":
        record["closed_at"] = time.time()
    dpr_store[cmp_request_id] = record
    _save(DPR_FILE, dpr_store)

    notification_id = f"notif-{uuid.uuid4().hex[:10]}"
    return {"acknowledged": True, "notification_id": notification_id}


@app.get("/dpr/{cmp_request_id}")
async def get_dpr(cmp_request_id: str):
    record = _load(DPR_FILE).get(cmp_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="unknown cmp_request_id")
    return record


@app.get("/health")
async def health():
    return {"status": "ok"}
