export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
export const SCRUTORA_SITE_KEY = process.env.NEXT_PUBLIC_SCRUTORA_SITE_KEY || "";
export const SCRUTORA_EMBED_SRC = SCRUTORA_SITE_KEY
  ? `https://api.scrutora.com/api/consent/embed/cs_${SCRUTORA_SITE_KEY}.js`
  : null;

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export type DsrRequestType = "access" | "correction" | "erasure" | "withdraw" | "grievance" | "nominate";
export type DsrResult = { ok: boolean; request_id: string; sla_due_at: string };

/** Calls Scrutora's DSR intake directly from the browser, matching their
 * own documented pattern -- it needs no secret, only the public site key
 * in the URL, and text/plain avoids a CORS preflight. */
export async function submitDsr(requestType: DsrRequestType, email: string, details?: string): Promise<DsrResult> {
  if (!SCRUTORA_SITE_KEY) throw new Error("NEXT_PUBLIC_SCRUTORA_SITE_KEY isn't set");
  const res = await fetch(`https://api.scrutora.com/api/consent/dsr/cs_${SCRUTORA_SITE_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: JSON.stringify({ request_type: requestType, email, details }),
  });
  if (!res.ok) throw new Error(`DSR submission failed -> ${res.status}`);
  return res.json();
}

declare global {
  interface Window {
    ScrutoraConsent?: {
      getConsent: () => { states: Record<string, boolean> } | undefined;
      openPreferences: () => void;
    };
  }
}

export type Tenant = { id: string; name: string };
export type Vehicle = {
  id: string;
  reg_number: string;
  route_name: string;
  driver_name: string | null;
  last_position: { lat: number; lon: number; speed_kmh: number; ts: string } | null;
};
export type Driver = { id: string; name: string; phone: string };
export type VideoEvent = {
  id: string;
  vehicle_id: string;
  driver_name: string | null;
  type: string;
  severity: string;
  clip_url: string | null;
  face_snapshot_url: string | null;
  ts: string;
};
export type VendorCall = {
  id: number;
  vendor: string;
  endpoint: string;
  method: string;
  payload_preview: Record<string, unknown>;
  driver_id: string | null;
  driver_name: string | null;
  ts: string;
};
export type DprStep = {
  step: number;
  name: string;
  status: string;
  evidence: Record<string, unknown> | null;
  ts: string;
};
export type DprRequest = {
  id: string;
  cmp_request_id: string;
  driver_id: string;
  trigger: string;
  status: string;
  opened_at: string;
  closed_at: string | null;
  steps: DprStep[];
};
