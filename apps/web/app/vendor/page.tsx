"use client";

import { useEffect, useState } from "react";
import { apiGet, VendorCall } from "@/lib/api";

type Holdings = { subjects: { subject_id: string; matched_driver_name: string | null }[] };

export default function VendorTrafficPage() {
  const [calls, setCalls] = useState<VendorCall[]>([]);
  const [holdings, setHoldings] = useState<Holdings>({ subjects: [] });

  async function refresh() {
    const [c, h] = await Promise.all([
      apiGet<VendorCall[]>("/vendor/calls"),
      apiGet<Holdings>("/vendor/holdings"),
    ]);
    setCalls(c);
    setHoldings(h);
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <h1 style={{ fontSize: 18, margin: 0 }}>Vendor Traffic — visionai_stub</h1>
      <p style={{ color: "#8b98a5", maxWidth: 640 }}>
        Every request Haulwise sends to its AI verification partner, and what that partner currently
        holds for each driver. This is the live proof of what leaves Haulwise and what the vendor keeps.
      </p>

      <div className="panel">
        <h2 style={{ fontSize: 14, color: "#8b98a5" }}>Vendor currently holds</h2>
        <table>
          <thead>
            <tr>
              <th>Subject ID (as sent to vendor)</th>
              <th>Matches a known driver name?</th>
            </tr>
          </thead>
          <tbody>
            {holdings.subjects.map((s) => (
              <tr key={s.subject_id}>
                <td>{s.subject_id}</td>
                <td>{s.matched_driver_name ? `yes — ${s.matched_driver_name}` : "no (pseudonymous)"}</td>
              </tr>
            ))}
            {holdings.subjects.length === 0 && (
              <tr>
                <td colSpan={2} style={{ color: "#8b98a5" }}>
                  Nothing held by the vendor right now.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2 style={{ fontSize: 14, color: "#8b98a5" }}>Request log</h2>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Driver</th>
              <th>Endpoint</th>
              <th>Payload sent</th>
            </tr>
          </thead>
          <tbody>
            {calls.map((c) => (
              <tr key={c.id}>
                <td>{new Date(c.ts).toLocaleTimeString()}</td>
                <td>{c.driver_name || "—"}</td>
                <td>{c.method} {c.endpoint}</td>
                <td>
                  <pre>{JSON.stringify(c.payload_preview, null, 2)}</pre>
                </td>
              </tr>
            ))}
            {calls.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: "#8b98a5" }}>
                  No vendor calls yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
