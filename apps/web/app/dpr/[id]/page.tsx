"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, DprRequest } from "@/lib/api";

export default function DprTimelinePage() {
  const params = useParams<{ id: string }>();
  const [dpr, setDpr] = useState<DprRequest | null>(null);

  useEffect(() => {
    let stop = false;
    async function poll() {
      const data = await apiGet<DprRequest>(`/dpr/${params.id}`);
      if (!stop) setDpr(data);
      if (!stop && data.status !== "closed") {
        setTimeout(poll, 1000);
      }
    }
    poll();
    return () => {
      stop = true;
    };
  }, [params.id]);

  if (!dpr) return <p>Loading...</p>;

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 720 }}>
      <div>
        <h1 style={{ fontSize: 18, margin: 0 }}>DPR request {dpr.cmp_request_id}</h1>
        <p style={{ color: "#8b98a5" }}>
          Trigger: {dpr.trigger} · Status: <strong>{dpr.status}</strong>
          {dpr.closed_at && ` · closed ${new Date(dpr.closed_at).toLocaleString()}`}
        </p>
      </div>

      <div className="panel">
        {dpr.steps.length === 0 && <p style={{ color: "#8b98a5" }}>No steps recorded yet.</p>}
        {dpr.steps.map((s) => (
          <div key={s.step} style={{ display: "flex", gap: 12, padding: "10px 0", borderBottom: "1px solid #232d38" }}>
            <div style={{ width: 24, color: "#8b98a5" }}>{s.step}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>{s.name}</span>
                <span className={`tag ${s.status === "done" ? "ok" : s.status === "failed" ? "high" : "pending"}`}>
                  {s.status}
                </span>
              </div>
              {s.evidence && (
                <pre style={{ marginTop: 6 }}>{JSON.stringify(s.evidence, null, 2)}</pre>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
