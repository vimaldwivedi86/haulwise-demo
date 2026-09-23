"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";

type VehicleDetail = {
  id: string;
  tenant_id: string;
  reg_number: string;
  route_name: string;
  driver: { id: string; name: string } | null;
};

export default function VehicleDetailPage() {
  const params = useParams<{ id: string }>();
  const [vehicle, setVehicle] = useState<VehicleDetail | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  useEffect(() => {
    apiGet<VehicleDetail>(`/vehicles/${params.id}`).then(setVehicle);
  }, [params.id]);

  async function createShareLink() {
    const res = await apiPost<{ token: string; url: string }>(`/vehicles/${params.id}/share`);
    setShareUrl(res.url);
  }

  if (!vehicle) return <p>Loading...</p>;

  return (
    <div className="panel" style={{ maxWidth: 480 }}>
      <h1 style={{ fontSize: 18 }}>{vehicle.reg_number}</h1>
      <p style={{ color: "#8b98a5" }}>{vehicle.route_name}</p>
      <p>Driver: {vehicle.driver?.name || "unassigned"}</p>

      <button
        onClick={createShareLink}
        style={{
          background: "#3b82f6",
          color: "white",
          border: "none",
          borderRadius: 8,
          padding: "10px 16px",
        }}
      >
        Create public tracking link
      </button>

      {shareUrl && (
        <div style={{ marginTop: 12 }}>
          <a href={shareUrl}>{shareUrl}</a>
        </div>
      )}
    </div>
  );
}
