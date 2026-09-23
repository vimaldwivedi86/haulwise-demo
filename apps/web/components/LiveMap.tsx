"use client";

import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";

const truckIcon = new L.DivIcon({
  className: "",
  html: '<div style="background:#3b82f6;width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 0 6px rgba(0,0,0,0.5)"></div>',
  iconSize: [14, 14],
});

export type MapVehicle = {
  id: string;
  reg_number: string;
  driver_name: string | null;
  lat: number;
  lon: number;
  speed_kmh: number;
};

function Recenter({ vehicles }: { vehicles: MapVehicle[] }) {
  const map = useMap();
  useEffect(() => {
    if (vehicles.length === 0) return;
    const bounds = L.latLngBounds(vehicles.map((v) => [v.lat, v.lon]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 9 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vehicles.length === 0]);
  return null;
}

export default function LiveMap({ vehicles }: { vehicles: MapVehicle[] }) {
  const center: [number, number] = vehicles.length
    ? [vehicles[0].lat, vehicles[0].lon]
    : [21.0, 78.0];

  return (
    <MapContainer center={center} zoom={7} style={{ height: "70vh", width: "100%", borderRadius: 10 }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Recenter vehicles={vehicles} />
      {vehicles.map((v) => (
        <Marker key={v.id} position={[v.lat, v.lon]} icon={truckIcon}>
          <Popup>
            <strong>{v.reg_number}</strong>
            <br />
            {v.driver_name}
            <br />
            {v.speed_kmh.toFixed(0)} km/h
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
