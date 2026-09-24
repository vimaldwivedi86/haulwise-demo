"""Client for the real Scrutora Consent Management Platform, per
https://scrutora.com/docs/consent (fetched 2026-09-24, cross-checked against
the integration guide pasted 2026-09-24 while wiring this up). Replaces the
local cmp_stub now that real API access is wired up.

DSR intake (POST /dsr/{site_key}) is called directly from the browser
(apps/web/app/driver/page.tsx), not through this module -- it needs no
Authorization header, only the public site key in the URL, exactly like
Scrutora's own documented example. There's nothing for a server-side
client to add there.

Known gaps against what the DPR workflow (dpr/orchestrator.py) wants, kept
here rather than papered over:
  - No documented endpoint for posting a DPR step status back to Scrutora.
    Orchestrator step 8 records that explicitly instead of pretending to
    call something that doesn't exist in the docs.
  - The DSR payload has no purpose field, so a purpose-scoped withdrawal
    can only be expressed via the free-text `details` field -- not a
    guarantee Scrutora scopes it that way server-side.
  - DSR intake identifies the requester by email; Haulwise identifies
    drivers by phone. The driver app's DSR form asks for an email
    separately rather than guessing one from the phone number on file.
"""

import os

import httpx

API_BASE_URL = os.environ.get("SCRUTORA_API_BASE_URL", "https://api.scrutora.com/api/consent")
API_KEY = os.environ.get("SCRUTORA_API_KEY", "")
SITE_ID = os.environ.get("SCRUTORA_SITE_ID", "")
SITE_KEY = os.environ.get("SCRUTORA_SITE_KEY", "")


def get_consent_state(identifier: str, identifier_type: str = "phone") -> dict:
    """GET /sites/{site_id}/state -- current purpose grants for one subject.
    Authenticated with the private API key, so this stays server-side."""
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{API_BASE_URL}/sites/{SITE_ID}/state",
            params={"identifier": identifier, "identifier_type": identifier_type},
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        resp.raise_for_status()
        return resp.json()
