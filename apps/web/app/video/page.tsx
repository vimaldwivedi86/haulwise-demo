"use client";

import { useEffect, useState } from "react";
import TenantSwitcher from "@/components/TenantSwitcher";
import { apiGet, Tenant, VideoEvent, WS_URL } from "@/lib/api";

export default function VideoSafetyPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [events, setEvents] = useState<VideoEvent[]>([]);

  useEffect(() => {
    apiGet<Tenant[]>("/tenants").then((rows) => {
      setTenants(rows);
      if (rows.length) setTenantId(rows[0].id);
    });
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    apiGet<VideoEvent[]>(`/video_events?tenant_id=${tenantId}`).then(setEvents);
  }, [tenantId]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/positions`);
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type !== "video_event") return;
      if (msg.tenant_id !== tenantId) return;
      apiGet<VideoEvent[]>(`/video_events?tenant_id=${tenantId}`).then(setEvents);
    };
    return () => ws.close();
  }, [tenantId]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: 18, margin: 0 }}>Video Safety</h1>
        <TenantSwitcher tenants={tenants} selected={tenantId} onChange={setTenantId} />
      </div>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
        {events.map((e) => (
          <div key={e.id} className="panel">
            {e.clip_url ? (
              <video src={e.clip_url} controls muted style={{ width: "100%", borderRadius: 6 }} />
            ) : (
              <div style={{ height: 150, background: "#0d1319", borderRadius: 6 }} />
            )}
            <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between" }}>
              <span>{e.type.replace("_", " ")}</span>
              <span className={`tag ${e.severity}`}>{e.severity}</span>
            </div>
            <div style={{ color: "#8b98a5", fontSize: 12, marginTop: 4 }}>
              {e.driver_name || "unassigned"} · {new Date(e.ts).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {events.length === 0 && <p style={{ color: "#8b98a5" }}>No events yet.</p>}
      </div>
    </div>
  );
}
