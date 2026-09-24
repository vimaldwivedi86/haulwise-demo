"""Client for the real Scrutora Consent Management Platform, per
https://scrutora.com/docs/consent (fetched 2026-09-24). Replaces the local
cmp_stub now that real API access is wired up.

Known gaps against what the DPR workflow (dpr/orchestrator.py) wants, kept
here rather than papered over:
  - No documented endpoint for posting a DPR step status back to Scrutora.
    Orchestrator step 8 records that explicitly instead of pretending to
    call something that doesn't exist in the docs.
  - The DSR payload (POST /dsr/{site_key}) has no purpose field, so a
    purpose-scoped withdrawal can only be expressed via the free-text
    `details` field -- not a guarantee Scrutora scopes it that way
    server-side. Confirm with Scrutora before relying on this for
    anything beyond this demo.
  - The DSR payload's identifying field shown in the docs is `email`;
    Haulwise identifies drivers by phone. Both are sent -- confirm which
    one Scrutora's backend actually expects.
"""

import os

import httpx

API_BASE_URL = os.environ.get("SCRUTORA_API_BASE_URL", "https://api.scrutora.com/api/consent")
API_KEY = os.environ.get("SCRUTORA_API_KEY", "")
SITE_ID = os.environ.get("SCRUTORA_SITE_ID", "")
SITE_KEY = os.environ.get("SCRUTORA_SITE_KEY", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {API_KEY}"}


def get_consent_state(identifier: str, identifier_type: str = "phone") -> dict:
    """GET /sites/{site_id}/state -- current purpose grants for one subject."""
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{API_BASE_URL}/sites/{SITE_ID}/state",
            params={"identifier": identifier, "identifier_type": identifier_type},
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


def create_dsr(request_type: str, email: str | None, phone: str | None, details: str | None = None) -> dict:
    """POST /dsr/{site_key} -- raise a Data Subject Request (access,
    correction, erasure, withdraw, grievance, nominate). Used as the
    server-side fallback for a purpose withdrawal; the primary path is the
    consent.withdrawn webhook fired by the embedded widget itself."""
    payload = {"request_type": request_type, "email": email, "phone": phone, "details": details}
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            f"{API_BASE_URL}/dsr/{SITE_KEY}",
            json=payload,
            headers={**_headers(), "Content-Type": "text/plain"},
        )
        resp.raise_for_status()
        return resp.json()
