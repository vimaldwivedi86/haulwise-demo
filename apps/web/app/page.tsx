"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import TenantSwitcher from "@/components/TenantSwitcher";
import { apiGet, Tenant, Vehicle, WS_URL } from "@/lib/api";
import type { MapVehicle } from "@/components/LiveMap";

const LiveMap = dynamic(() => import("@/components/LiveMap"), { ssr: false });

export default function LiveMapPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState<string>("");
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [live, setLive] = useState<Record<string, { lat: number; lon: number; speed_kmh: number }>>({});

  useEffect(() => {
    apiGet<Tenant[]>("/tenants").then((rows) => {
      setTenants(rows);
      if (rows.length) setTenantId(rows[0].id);
    });
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    apiGet<Vehicle[]>(`/vehicles?tenant_id=${tenantId}`).then(setVehicles);
  }, [tenantId]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/positions`);
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type !== "position") return;
      setLive((prev) => ({
        ...prev,
        [msg.vehicle_id]: { lat: msg.lat, lon: msg.lon, speed_kmh: msg.speed_kmh },
      }));
    };
    return () => ws.close();
  }, []);

  const mapVehicles: MapVehicle[] = useMemo(
    () =>
      vehicles
        .filter((v) => live[v.id] || v.last_position)
        .map((v) => {
          const pos = live[v.id] || v.last_position!;
          return {
            id: v.id,
            reg_number: v.reg_number,
            driver_name: v.driver_name,
            lat: pos.lat,
            lon: pos.lon,
            speed_kmh: pos.speed_kmh,
          };
        }),
    [vehicles, live]
  );

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: 18, margin: 0 }}>Live Map</h1>
        <TenantSwitcher tenants={tenants} selected={tenantId} onChange={setTenantId} />
      </div>
      <div className="panel">
        <LiveMap vehicles={mapVehicles} />
      </div>
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>Driver</th>
              <th>Speed</th>
            </tr>
          </thead>
          <tbody>
            {mapVehicles.map((v) => (
              <tr key={v.id}>
                <td>{v.reg_number}</td>
                <td>{v.driver_name}</td>
                <td>{v.speed_kmh.toFixed(0)} km/h</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
