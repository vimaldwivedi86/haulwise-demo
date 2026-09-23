# Haulwise: Demo Fleet App for Scrutora

Tech spec for Claude Code plus the demo run of show. Build 24 Sep 2026, demo 25 Sep, 15 minute slot (20 at best).

## 1. Goal

A small fictional fleet platform, **Haulwise**, with live GPS, AI dashcam events, a shareable tracking link and a driver consent lifecycle. The centrepiece is one story:

1. A driver gives consent for face verification through the Scrutora CMP.
2. Haulwise sends his face image to an AI vendor, raw and unmasked. Scrutora's AI scan flags it.
3. The driver withdraws consent. The Scrutora CMP raises a Data Principal Rights (DPR) request, and a workflow carries out everything his withdrawal requires: stop processing, delete, tell the processor to delete, keep only what law requires, confirm back to him, close with evidence.

On `main`, withdrawal only flips a flag and the face data keeps flowing. On `compliant`, the full workflow runs. The audience watches both.

Two supporting findings cover the other audiences: a public tracking link (business) and a missing tenant filter (engineering).

## 2. Rules for Claude Code (put in `CLAUDE.md`)

1. No comments that hint at seeded issues.
2. Answer key lives outside the repo at `../haulwise_answer_key.md`.
3. Synthetic data only: Faker `en_IN`, generated phones, placeholder avatars, ffmpeg generated clips. No real faces.
4. No real brand names or UI. Tenants: `Aravalli Cement`, `Konkan Foods`.
5. `docker compose up` runs everything within 2 minutes.
6. Branches: `main` with the seeded issues, `compliant` with one fix commit per issue.

## 3. Stack

Confirm Scrutora supports each.

| Part | Choice |
|---|---|
| Web | Next.js 14 (TypeScript), Leaflet with OpenStreetMap |
| API | Python FastAPI, SQLAlchemy, WebSocket |
| Ingest | Python MQTT consumer to Postgres and Redis |
| Simulator | Python, GPS and dashcam events over MQTT |
| Infra | Postgres, Mosquitto, MinIO, Redis via docker compose |
| AI vendor stub | `visionai_stub` FastAPI: `POST /v1/face/verify`, `DELETE /v1/subjects/{id}`. Stores what it receives in its own volume so deletion is real and visible |
| Consent and DPR | Scrutora CMP: purpose level consent, receipts, withdrawal, DPR request |
| CI | GitHub Actions with Scrutora, private repo |

## 4. Layout

```
haulwise/
  CLAUDE.md
  docker-compose.yml
  Makefile
  .github/workflows/scrutora.yml
  apps/web/
  services/api/
    routes/share.py
    routes/positions.py
    face.py
    consent_webhook.py
    dpr/orchestrator.py
  services/ingest/
  services/simulator/
  services/visionai_stub/
  config/processors.yaml
  config/retention.yaml
  db/migrations/
  db/seed/
```

## 5. Data model

`tenants`, `drivers` (tenant_id, name, phone, dl_number, face_image_key, face_embedding), `vehicles`, `positions`, `video_events` (vehicle_id, driver_id, type, severity, clip_key, face_snapshot_key, ts), `share_links`, `consents` (driver_id, purpose, status, receipt_id, ts), `dpr_requests` (id, cmp_request_id, driver_id, trigger, status, opened_at, closed_at), `dpr_steps` (dpr_id, step, status, evidence, ts), `vendor_calls` (vendor, endpoint, payload_preview, ts).

Consent purposes: `trip_tracking`, `safety_video`, `face_verification`.

## 6. Screens

1. **Live Map** (`/`): tenant switcher, trucks moving on NH48 and the Mumbai Pune Expressway.
2. **Video Safety** (`/video`): event feed with synthetic clips. Face mismatch events call the vendor.
3. **Share Tracking** (`/vehicles/[id]`, public `/t/[linkId]`).
4. **Driver App** (`/driver`): phone frame. Consent screen via Scrutora CMP (English and Hindi), receipt view, "Withdraw face verification" button.
5. **Vendor Traffic** (`/vendor`): live log of every request to `visionai_stub` with payload preview, plus what the vendor currently holds for each driver. This panel is the visual proof: on `main` it shows name, phone and raw image going out and staying there, and on `compliant` it shows a pseudonymous ID and the vendor's copy disappearing after withdrawal.
6. **DPR Timeline** (`/dpr/[id]`): step by step status of the withdrawal workflow with evidence per step. If the Scrutora CMP can display downstream step status natively, show it there instead and keep this page as the fallback.

## 7. Consent lifecycle and DPR workflow

### 7.1 Consent given
Driver accepts `face_verification` in the CMP. CMP issues a hash chained receipt and sends `consent.granted` to `consent_webhook.py`. Haulwise stores the receipt ID.

### 7.2 Data flows to the AI vendor
On onboarding and on every face mismatch event, `face.py` calls `visionai_stub`.

### 7.3 Driver withdraws
CMP records the withdrawal, appends to the receipt chain, raises a DPR request, and sends `consent.withdrawn` to Haulwise with the DPR ID.

### 7.4 Workflow run by `dpr/orchestrator.py` (compliant branch)

| Step | Action | Evidence recorded | Why |
|---|---|---|---|
| 1 | Verify webhook signature, link to CMP DPR ID | Signature check result | Authenticity |
| 2 | Stop processing: face calls for this driver blocked immediately | Blocked call count after withdrawal | DPDP §6(6): cease processing within reasonable time |
| 3 | Delete face image from MinIO and embedding from `drivers` | Object keys deleted, row updated | Purpose no longer served, §8(7) |
| 4 | Strip face snapshots from past `video_events`, keep event metadata and road facing clip | Count of snapshots removed | Delete only what the withdrawn purpose covered |
| 5 | Instruct the processor: `DELETE /v1/subjects/{id}` on the vendor, wait for acknowledgement | Vendor acknowledgement ID | §6(6) requires causing processors to cease too |
| 6 | Retention check against `retention.yaml`: anything under legal hold or another valid purpose is kept and listed with its basis | Retained items with legal basis | Withdrawal does not override data required by law |
| 7 | Leave other purposes untouched (`trip_tracking`, `safety_video` stay active) | Purpose status snapshot | Withdrawal is purpose specific |
| 8 | Post status back to the CMP, CMP notifies the driver of the outcome | CMP DPR status, notification ID | Transparency to the Data Principal |
| 9 | Close DPR with an evidence pack (JSON plus PDF) | Evidence pack link | Proof for audits and grievance handling |

Citations are candidates: confirm §6(6), §8(7) and §12 wording against Scrutora's mapping before the call.

### 7.5 Main branch behaviour (seeded)
`consent_webhook.py` updates the `consents` row and nothing else. `face.py` never checks consent. No DPR orchestrator exists. After withdrawal, face mismatch events keep sending his image to the vendor, and the vendor keeps its copy.

## 8. Seeded issues

| # | For | Where | Seeded on `main` | Fix on `compliant` | Scrutora capability |
|---|---|---|---|---|---|
| 1 | Mohit, Shantanu | `face.py` | Face image, name, phone and DL number sent over plain HTTP to the AI vendor. No masking, no pseudonymisation. Vendor missing from `processors.yaml` | HTTPS, pseudonymous subject ID only, vendor declared with purpose and region | AI SAST, dataflow, RoPA |
| 2 | Mohit | `face.py`, `consent_webhook.py` | Face processing not gated on `face_verification` consent. Withdrawal does not stop processing or reach the vendor | Consent gate plus DPR orchestrator (section 7.4) | Consent to code matching, DSR fulfilment |
| 3 | Vineet, Rishav | `routes/share.py` | Public link: sequential ID, no expiry, driver name and phone exposed | UUID, 24 hour expiry, position and ETA only | Dataflow, code control mapping |
| 4 | Shantanu | `routes/positions.py` | No tenant filter on position history | Tenant scoped dependency | Code control mapping |

Issues 1 and 2 are the consent story. Issues 3 and 4 are one slide each in the demo.

## 9. CI

`.github/workflows/scrutora.yml` on push for both branches, SARIF uploaded. Secret name from `https://www.scrutora.com/docs/ci-cd`.

## 10. Build plan (about 6.5 hours)

| Step | Est. |
|---|---|
| Compose stack, migrations, seed | 45 min |
| Simulator, ingest, WebSocket, screens 1 to 3 | 2 h |
| Vendor stub with storage and delete, Vendor Traffic screen | 45 min |
| CMP integration: consent, receipt, withdrawal webhook (hard stop 1 h) | 1 h |
| DPR orchestrator and timeline screen | 1.25 h |
| Seed issues, `compliant` branch, CI, dry run | 45 min |

**Before building, confirm with Satish or the product:** does the Scrutora CMP send outbound webhooks on withdrawal, and can external systems post DPR step status back? If not, Haulwise polls the CMP API or the demo shows the DPR timeline on Haulwise's side only. Do not show the CMP doing something it cannot.

## 11. Acceptance (tomorrow night)

1. Trucks move within 2 minutes.
2. On `main`: withdraw consent, then `make burst`. The Vendor Traffic panel shows face data still going out.
3. On `compliant`: withdraw consent. All 9 steps complete, vendor copy gone, other purposes intact, DPR closed with evidence pack.
4. Scrutora flags issues 1 to 4 on `main` with correct clauses, none on `compliant`.
5. Extra findings reviewed, false positives fixed.
6. Two app instances ready (`main` on port 3000, `compliant` on 3001) and both scans open in tabs. Never wait on CI live.
7. Full screen recording saved as backup.

## 12. Run of show (15 minutes)

| Min | Segment | Lands with | What you do |
|---|---|---|---|
| 0 to 2 | Open | Everyone | Congratulate them on Pando. Ask Vineet: "What made this worth an hour now?" |
| 2 to 3 | Thesis | Everyone | "Your privacy policy promises drivers control over their data. We show whether the code honours it." |
| 3 to 4 | Live app | Everyone | Map, burst, clip plays |
| 4 to 5 | Consent given | Mohit | Driver consents to face verification in the CMP, receipt shown |
| 5 to 6 | AI finding | Mohit, Shantanu | Vendor Traffic panel: raw face, name, phone going out. Scrutora finding with clause |
| 6 to 7 | Withdrawal on `main` | Everyone | Driver withdraws, burst, face data still flows. Let it sit for five seconds |
| 7 to 9 | Withdrawal on `compliant` | Mohit, Vineet | Same action. DPR opens, 9 steps tick through, vendor copy deleted, trip tracking untouched, evidence pack |
| 9 to 10 | Issues 3 and 4 | Rishav, Shantanu | One finding each, 30 seconds each |
| 10 to 11 | Scan facts | Shantanu | Scan time, zero code retention, CI fit |
| 11 to 15 | Close | Vineet, Rishav | 4 week pilot on one Fleetx repo and one Pando repo, success criteria, named owner, next date |

If you get 20 minutes, use the extra 5 for questions. Don't add demo.

Scrutora scans code, not live streams or video. Say so if asked.
