"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet } from "@/lib/api";

type SharedTrack = {
  reg_number: string | null;
  driver_name?: string | null;
  driver_phone?: string | null;
  position: { lat: number; lon: number; ts: string } | null;
};

export default function PublicTrackingPage() {
  const params = useParams<{ linkId: string }>();
  const [data, setData] = useState<SharedTrack | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiGet<SharedTrack>(`/t/${params.linkId}`)
      .then(setData)
      .catch(() => setError(true));
  }, [params.linkId]);

  if (error) return <p>This tracking link is invalid or has expired.</p>;
  if (!data) return <p>Loading...</p>;

  return (
    <div className="panel" style={{ maxWidth: 420 }}>
      <h1 style={{ fontSize: 18 }}>{data.reg_number}</h1>
      {data.driver_name && <p>Driver: {data.driver_name}</p>}
      {data.driver_phone && <p>Phone: {data.driver_phone}</p>}
      {data.position ? (
        <p>
          Last seen {data.position.lat.toFixed(4)}, {data.position.lon.toFixed(4)} at{" "}
          {new Date(data.position.ts).toLocaleTimeString()}
        </p>
      ) : (
        <p>No position yet.</p>
      )}
    </div>
  );
}
