"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import TenantSwitcher from "@/components/TenantSwitcher";
import { apiGet, cmpGet, cmpPost, Driver, DprRequest, Tenant } from "@/lib/api";
import { COPY, Lang } from "@/lib/i18n";

type Receipt = {
  receipt_id: string;
  seq: number;
  purpose: string;
  action: string;
  ts: number;
  hash: string;
};

type ConsentMap = Record<string, { status: string; receipt_id: string | null; ts: string }>;

export default function DriverAppPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [driverId, setDriverId] = useState("");
  const [consents, setConsents] = useState<ConsentMap>({});
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [dprList, setDprList] = useState<DprRequest[]>([]);
  const [lang, setLang] = useState<Lang>("en");
  const [busy, setBusy] = useState(false);

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
    const [c, r, d] = await Promise.all([
      apiGet<ConsentMap>(`/drivers/${id}/consents`),
      cmpGet<Receipt[]>(`/receipts/${id}`),
      apiGet<DprRequest[]>(`/dpr?driver_id=${id}`),
    ]);
    setConsents(c);
    setReceipts(r);
    setDprList(d);
  }

  useEffect(() => {
    if (driverId) refresh(driverId);
  }, [driverId]);

  const faceConsent = consents["face_verification"];
  const isGranted = faceConsent?.status === "granted";

  async function act(action: "grant" | "withdraw") {
    setBusy(true);
    try {
      await cmpPost(`/consent/${action}`, { driver_id: driverId, purpose: "face_verification" });
      await new Promise((r) => setTimeout(r, 400));
      await refresh(driverId);
    } finally {
      setBusy(false);
    }
  }

  const t = COPY[lang];

  return (
    <div className="grid" style={{ gap: 16 }}>
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

      <div className="phone-frame">
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
          <button onClick={() => setLang(lang === "en" ? "hi" : "en")} style={{ background: "none", border: "1px solid #232d38", color: "#8b98a5", borderRadius: 6, padding: "4px 10px" }}>
            {lang === "en" ? "हिंदी" : "English"}
          </button>
        </div>

        <h2 style={{ fontSize: 16 }}>{t.title}</h2>
        <p style={{ color: "#8b98a5", fontSize: 13, lineHeight: 1.5 }}>{t.body}</p>

        <div style={{ margin: "16px 0" }}>
          <span className={`tag ${isGranted ? "ok" : "pending"}`}>
            {isGranted ? t.granted : t.withdrawn}
          </span>
        </div>

        {!isGranted ? (
          <button
            disabled={busy}
            onClick={() => act("grant")}
            style={{ width: "100%", background: "#3b82f6", color: "white", border: "none", borderRadius: 8, padding: "12px" }}
          >
            {t.grant}
          </button>
        ) : (
          <button
            disabled={busy}
            onClick={() => act("withdraw")}
            style={{ width: "100%", background: "#ef4444", color: "white", border: "none", borderRadius: 8, padding: "12px" }}
          >
            {t.withdraw}
          </button>
        )}

        <div style={{ marginTop: 20 }}>
          <h3 style={{ fontSize: 13, color: "#8b98a5" }}>{t.receipts}</h3>
          {receipts.map((r) => (
            <div key={r.receipt_id} style={{ fontSize: 12, borderBottom: "1px solid #232d38", padding: "6px 0" }}>
              <div>{r.receipt_id} — {r.action}</div>
              <div style={{ color: "#8b98a5" }}>{new Date(r.ts * 1000).toLocaleString()}</div>
            </div>
          ))}
          {receipts.length === 0 && <p style={{ color: "#8b98a5", fontSize: 12 }}>No receipts yet.</p>}
        </div>

        {dprList.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <h3 style={{ fontSize: 13, color: "#8b98a5" }}>{t.dpr}</h3>
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
