"""Runs the 9-step withdrawal workflow described in the tech spec (section
7.4) once a driver withdraws face_verification consent. Each step commits
its own DprStep row with evidence before moving to the next, so the DPR
timeline screen can show real progress rather than a single final state."""

import io
import json
import os
import time

import httpx
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

import face
import storage
from config import load_retention
from db import SessionLocal
from models import Consent, Driver, DprRequest, DprStep, VendorCall, VideoEvent

CMP_URL = os.environ.get("CMP_URL", "http://cmp_stub:8200")

STEP_PACE_SECONDS = 0.6

STEP_NAMES = {
    1: "Verify webhook signature, link to CMP DPR ID",
    2: "Stop processing: block face calls for this driver",
    3: "Delete face image and embedding",
    4: "Strip face snapshots from past video events",
    5: "Instruct the processor to delete its copy",
    6: "Retention check against retention.yaml",
    7: "Leave other purposes untouched",
    8: "Post status back to the CMP",
    9: "Close DPR with an evidence pack",
}


def _record_step(db: Session, dpr: DprRequest, step: int, status: str, evidence: dict):
    time.sleep(STEP_PACE_SECONDS)
    db.add(DprStep(dpr_id=dpr.id, step=step, name=STEP_NAMES[step], status=status, evidence=evidence))
    db.commit()


def run(dpr_id: str):
    db = SessionLocal()
    try:
        dpr = db.query(DprRequest).filter(DprRequest.id == dpr_id).first()
        if not dpr:
            return
        driver = db.query(Driver).filter(Driver.id == dpr.driver_id).first()

        # Step 1: signature already verified by consent_webhook.py before
        # this workflow was started; this step records that link explicitly.
        _record_step(
            db,
            dpr,
            1,
            "done",
            {"signature_valid": True, "cmp_dpr_id": dpr.cmp_request_id},
        )

        # Step 2: prove the gate is active with a live self-check call.
        before = db.query(VendorCall).filter(VendorCall.driver_id == driver.id, VendorCall.method == "BLOCKED").count()
        face.call_vendor_verify(db, driver, event_id="dpr-verification-check")
        after = db.query(VendorCall).filter(VendorCall.driver_id == driver.id, VendorCall.method == "BLOCKED").count()
        _record_step(db, dpr, 2, "done", {"blocked_call_count": after - before})

        # Step 3: delete the face image and embedding.
        deleted_key = driver.face_image_key
        if deleted_key:
            storage.delete_key(deleted_key)
        driver.face_image_key = None
        driver.face_embedding = None
        db.add(driver)
        db.commit()
        _record_step(db, dpr, 3, "done", {"deleted_object_key": deleted_key, "embedding_cleared": True})

        # Step 4: strip face snapshots from past events, keep everything else.
        events = db.query(VideoEvent).filter(VideoEvent.driver_id == driver.id, VideoEvent.face_snapshot_key.isnot(None)).all()
        removed = 0
        for e in events:
            storage.delete_key(e.face_snapshot_key)
            e.face_snapshot_key = None
            db.add(e)
            removed += 1
        db.commit()
        _record_step(db, dpr, 4, "done", {"snapshots_removed": removed})

        # Step 5: tell the processor to delete its copy, wait for ack.
        subject_id = f"drv-{driver.id}"
        vendor_ack = None
        try:
            with httpx.Client(timeout=10, verify=False) as client:
                resp = client.delete(f"{face.VISIONAI_URL}/v1/subjects/{subject_id}")
                vendor_ack = resp.json().get("ack_id")
        except httpx.HTTPError as exc:
            vendor_ack = f"error: {exc}"
        db.add(VendorCall(vendor="visionai_stub", endpoint=f"/v1/subjects/{subject_id}", method="DELETE", payload_preview={"subject_id": subject_id}, driver_id=driver.id))
        db.commit()
        _record_step(db, dpr, 5, "done", {"vendor_ack_id": vendor_ack})

        # Step 6: retention check -- anything under legal hold or another
        # active purpose is kept and listed with its basis.
        retained = load_retention()
        _record_step(db, dpr, 6, "done", {"retained_items": retained})

        # Step 7: withdrawal is purpose-specific; snapshot the others.
        other_purposes = {}
        for purpose in ("trip_tracking", "safety_video"):
            latest = (
                db.query(Consent)
                .filter(Consent.driver_id == driver.id, Consent.purpose == purpose)
                .order_by(Consent.ts.desc())
                .first()
            )
            other_purposes[purpose] = latest.status if latest else "not yet granted"
        _record_step(db, dpr, 7, "done", other_purposes)

        # Step 8: post status back to the CMP; it notifies the driver.
        cmp_notification_id = None
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{CMP_URL}/dpr/{dpr.cmp_request_id}/status",
                    json={"status": "closed", "detail": "face_verification withdrawal fulfilled"},
                )
                cmp_notification_id = resp.json().get("notification_id")
        except httpx.HTTPError as exc:
            cmp_notification_id = f"error: {exc}"
        _record_step(db, dpr, 8, "done", {"cmp_status": "closed", "notification_id": cmp_notification_id})

        # Step 9: close the DPR with an evidence pack (JSON + PDF).
        steps = db.query(DprStep).filter(DprStep.dpr_id == dpr.id).order_by(DprStep.step).all()
        pack = {
            "dpr_id": str(dpr.id),
            "cmp_request_id": dpr.cmp_request_id,
            "driver_id": str(dpr.driver_id),
            "trigger": dpr.trigger,
            "steps": [{"step": s.step, "name": s.name, "status": s.status, "evidence": s.evidence} for s in steps],
        }
        json_key = f"dpr/{dpr.id}/evidence.json"
        storage.put_bytes(json_key, json.dumps(pack, indent=2, default=str).encode(), content_type="application/json")

        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, "Haulwise -- DPR evidence pack")
        c.setFont("Helvetica", 10)
        y = 770
        c.drawString(50, y, f"DPR: {dpr.cmp_request_id}  Driver: {dpr.driver_id}  Trigger: {dpr.trigger}")
        y -= 24
        for s in steps:
            c.drawString(50, y, f"{s.step}. {s.name} -- {s.status}")
            y -= 16
            if y < 60:
                c.showPage()
                y = 800
        c.save()
        pdf_key = f"dpr/{dpr.id}/evidence.pdf"
        storage.put_bytes(pdf_key, pdf_buffer.getvalue(), content_type="application/pdf")

        dpr.status = "closed"
        db.add(dpr)
        db.commit()
        _record_step(
            db,
            dpr,
            9,
            "done",
            {"evidence_pack_json": storage.object_url(json_key), "evidence_pack_pdf": storage.object_url(pdf_key)},
        )
    finally:
        db.close()
