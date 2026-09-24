"use client";

import Script from "next/script";
import { useEffect, useState } from "react";
import Link from "next/link";
import TenantSwitcher from "@/components/TenantSwitcher";
import { apiGet, Driver, DprRequest, SCRUTORA_EMBED_SRC, Tenant } from "@/lib/api";

type ScrutoraState = {
  found?: boolean;
  purposes?: Record<string, boolean>;
  status?: string;
  collected_at?: string;
};

export default function DriverAppPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [driverId, setDriverId] = useState("");
  const [scrutoraState, setScrutoraState] = useState<ScrutoraState | null>(null);
  const [dprList, setDprList] = useState<DprRequest[]>([]);

  useEffect(() => {
    apiGet<Tenant[]>("/tenants").then((rows) => {
      setTenants(rows);
      if (rows.length) setTenantId(rows[0].id);
    });
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    apiGet<Driver[]>(`/drivers?tenant_id=${tenantId}`).then((rows) => {
      setDrivers(rows);
      if (rows.length) setDriverId(rows[0].id);
    });
  }, [tenantId]);

  async function refresh(id: string) {
    const [state, dpr] = await Promise.all([
      apiGet<ScrutoraState>(`/drivers/${id}/scrutora-state`).catch(() => null),
      apiGet<DprRequest[]>(`/dpr?driver_id=${id}`),
    ]);
    setScrutoraState(state);
    setDprList(dpr);
  }

  useEffect(() => {
    if (!driverId) return;
    refresh(driverId);
    // Polls rather than hooking a widget event, since the docs don't
    // document one for "a purpose just changed."
    const interval = setInterval(() => refresh(driverId), 3000);
    return () => clearInterval(interval);
  }, [driverId]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      {SCRUTORA_EMBED_SRC && <Script src={SCRUTORA_EMBED_SRC} strategy="afterInteractive" />}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: 18, margin: 0 }}>Driver App</h1>
        <div style={{ display: "flex", gap: 12 }}>
          <TenantSwitcher tenants={tenants} selected={tenantId} onChange={setTenantId} />
          <select
            value={driverId}
            onChange={(e) => setDriverId(e.target.value)}
            style={{ background: "#131a22", color: "#e6edf3", border: "1px solid #232d38", borderRadius: 8, padding: "8px 12px" }}
          >
            {drivers.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!SCRUTORA_EMBED_SRC && (
        <div className="panel" style={{ color: "#8b98a5" }}>
          NEXT_PUBLIC_SCRUTORA_SITE_KEY isn&apos;t set, so the Scrutora consent widget can&apos;t load. Set it and
          rebuild the web image to capture consent here.
        </div>
      )}

      <div className="phone-frame">
        <p style={{ color: "#8b98a5", fontSize: 13, lineHeight: 1.5 }}>
          Consent is captured by Scrutora&apos;s own widget. Use its banner, or the button below to reopen its
          preferences panel and change a purpose.
        </p>

        <button
          onClick={() => window.ScrutoraConsent?.openPreferences()}
          disabled={!SCRUTORA_EMBED_SRC}
          style={{ width: "100%", background: "#3b82f6", color: "white", border: "none", borderRadius: 8, padding: "12px" }}
        >
          Manage consent preferences
        </button>

        <div style={{ marginTop: 20 }}>
          <h3 style={{ fontSize: 13, color: "#8b98a5" }}>Current state (from Scrutora)</h3>
          {scrutoraState?.purposes ? (
            Object.entries(scrutoraState.purposes).map(([purpose, granted]) => (
              <div key={purpose} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, borderBottom: "1px solid #232d38", padding: "6px 0" }}>
                <span>{purpose}</span>
                <span className={`tag ${granted ? "ok" : "pending"}`}>{granted ? "granted" : "withdrawn"}</span>
              </div>
            ))
          ) : (
            <p style={{ color: "#8b98a5", fontSize: 12 }}>No state on record yet for this driver.</p>
          )}
        </div>

        {dprList.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <h3 style={{ fontSize: 13, color: "#8b98a5" }}>Your data request</h3>
            {dprList.map((d) => (
              <Link key={d.id} href={`/dpr/${d.id}`} style={{ display: "block", fontSize: 13, padding: "6px 0" }}>
                {d.status === "closed" ? "✓" : "…"} {d.trigger} — {d.status}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
