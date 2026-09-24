# Haulwise: Demo Fleet App for Scrutora

Tech spec for Claude Code plus the demo run of show. Build 24 Sep 2026, demo 25 Sep, 15 minute slot (20 at best).

**Status: built and verified locally on 2026-09-24.** All sections below are updated to reflect what was actually implemented, not just planned. Three items need a human before the real demo, detailed in the sections they touch: the Scrutora CMP integration (section 3), the CI secret name (section 9), and the DPDP citation wording (section 7.4). None were guessed at; each is either built against a clearly-labelled stand-in or left as a flagged placeholder.

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

As built, all six rules hold: `main` has one commit per seeded issue's fix on `compliant`, seed data is deterministic Faker `en_IN` (fixed seed), and the answer key is at `../haulwise_answer_key.md`, outside this repo.

## 3. Stack

Confirm Scrutora supports each. As built, every row matches this table except Consent and DPR -- see the note below it.

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

**Consent and DPR, as built:** no credentials or API access to the real Scrutora CMP were available during the build, so `services/cmp_stub/` stands in for it end to end -- purpose level consent, a hash chained receipt log, withdrawal, DPR request creation, an outbound signed webhook to Haulwise, and an endpoint Haulwise posts DPR step status back to. It answers the open question in section 10 (outbound webhooks and step status intake) by construction, since Haulwise's own team controls it. This still needs to be swapped for the real Scrutora CMP integration, and the run of show re-verified against it, before the actual demo.

**Infra note:** MinIO's images (`minio/minio`, `minio/mc`) moved off Docker Hub; the compose files pull `quay.io/minio/minio` and `quay.io/minio/mc` instead. Confirmed working as of this build.

## 4. Layout

As built (repo root is `haulwise_demo/`, matching this layout one level down):

```
haulwise_demo/
  CLAUDE.md
  docker-compose.yml
  Makefile
  .github/workflows/scrutora.yml
  apps/web/
    app/ (page.tsx, video/, vehicles/[id]/, t/[linkId]/, driver/, vendor/, dpr/[id]/)
    components/ (LiveMap.tsx, TenantSwitcher.tsx)
    lib/ (api.ts, i18n.ts)
  services/api/
    routes/ (tenants.py, vehicles.py, positions.py, share.py, drivers.py, video_events.py, vendor_log.py, dpr.py)
    dpr/orchestrator.py  -- compliant branch only, see 7.5
    face.py, consent_webhook.py, deps.py, eta.py, storage.py, avatar.py, config.py
    db.py, db_migrate.py, db_seed.py, models.py, main.py
  services/ingest/
  services/simulator/ (main.py, burst.py, clips.py, routes.py, mqtt_client.py)
  services/visionai_stub/ (dual HTTP :8100 / HTTPS :8143 listeners, self-signed cert)
  services/cmp_stub/  -- stands in for the real Scrutora CMP, see section 3
  config/processors.yaml
  config/retention.yaml
  db/migrations/ (numbered .sql files, applied by db_migrate.py)
  db/seed/ (routes.json fixture; db_seed.py itself lives in services/api/)
```

`api` runs its own migrations and seed on container startup (`start.sh`), so a bare `docker compose up` is self-sufficient per rule 5, without a separate manual step.

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

Citations are candidates: confirm §6(6), §8(7) and §12 wording against Scrutora's mapping before the call. As built, every place a citation is shown -- `config/retention.yaml` and the step 6 evidence it feeds -- is labelled "candidate citation, confirm against Scrutora's mapping" rather than asserted as verified, since that confirmation wasn't available during the build.

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

**Implementation notes:**
- Issue 1's HTTPS fix is served by `visionai_stub` itself, over a second listener on a self-signed certificate generated at image build time (`services/visionai_stub/entrypoint.sh`). This proves out the code-level control (the client calls `https://`, not `http://`) but is not a CA-signed cert; a real deployment would trust a real CA.
- Issue 2's pseudonymous subject ID is `drv-{driver.id}`; the vendor never sees a name, phone, or DL number once consent is withdrawn or was never granted.
- Issue 4's "tenant scoped dependency" is an `X-Tenant-Id` header dependency (`services/api/deps.py`) standing in for a real auth/session layer, which this demo doesn't have. It 401s with no header and 404s if the header's tenant doesn't own the requested vehicle.
- All four issues, and their fixes, were exercised live end to end (see section 11).

## 9. CI

`.github/workflows/scrutora.yml` on push for both branches, SARIF uploaded via `github/codeql-action/upload-sarif@v3`. Secret name from `https://www.scrutora.com/docs/ci-cd`.

**As built:** that page was fetched during the build to get the real secret name rather than guess it. The result (a secret named `SECUREHEALTH_API_KEY`, host `api.scrutora.com`) doesn't match the Scrutora brand and reads as untrustworthy -- possibly a stale or wrong page, possibly worse. It was not used. The workflow instead uses a placeholder (`SCRUTORA_API_KEY`) with a `TODO` comment, and the actual Scrutora scan invocation step is a stub. Both need the real product docs, with human access, before this job can run a real scan.

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

**As built:** that confirmation wasn't available during the build, so this question was answered by building `services/cmp_stub/` (section 3) rather than assumed either way. It sends outbound webhooks and accepts step status back because Haulwise's own team built it that way for this demo -- which says nothing about whether the real Scrutora CMP does. Re-confirm against the real product before the actual demo, and swap the stub out if the answer differs.

## 11. Acceptance (tomorrow night)

1. Trucks move within 2 minutes. **Verified 2026-09-24:** `docker compose up` alone brings up migrations, seed, and moving trucks with no manual steps.
2. On `main`: withdraw consent, then `make burst`. The Vendor Traffic panel shows face data still going out. **Verified:** all 6 seeded drivers' raw name/phone/DL data kept flowing to the vendor after withdrawal.
3. On `compliant`: withdraw consent. All 9 steps complete, vendor copy gone, other purposes intact, DPR closed with evidence pack. **Verified:** all 9 `dpr_steps` completed with real evidence; the vendor's own storage was confirmed empty afterward (not just a status code); the evidence pack JSON and PDF were both fetched successfully from MinIO; a post-withdrawal `make burst` blocked every call, including drivers who'd never granted consent.
4. Scrutora flags issues 1 to 4 on `main` with correct clauses, none on `compliant`. **Not yet run** -- needs an actual Scrutora scan against the repo, outside this build session.
5. Extra findings reviewed, false positives fixed. **Not yet run**, same reason as above.
6. Two app instances ready (`main` on port 3000, `compliant` on 3001) and both scans open in tabs. Never wait on CI live. **As built:** `compliant` is on 3001 as specified. `main` ran on 3010 during this build because port 3000 was already occupied by an unrelated process on the build machine -- confirm 3000 is free on the actual demo machine, or adjust `docker-compose.yml`'s `web` port mapping there. Running both branches simultaneously needs two separate working-tree checkouts of this repo (e.g. `git worktree add ../haulwise_compliant compliant`), since only one branch can be checked out in a single directory at a time; each branch's compose file already has a distinct project name and non-overlapping host ports.
7. Full screen recording saved as backup. **Not yet done.**

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
