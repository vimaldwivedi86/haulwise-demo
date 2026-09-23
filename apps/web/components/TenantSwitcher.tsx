"use client";

import { Tenant } from "@/lib/api";

export default function TenantSwitcher({
  tenants,
  selected,
  onChange,
}: {
  tenants: Tenant[];
  selected: string;
  onChange: (id: string) => void;
}) {
  return (
    <select
      value={selected}
      onChange={(e) => onChange(e.target.value)}
      style={{
        background: "#131a22",
        color: "#e6edf3",
        border: "1px solid #232d38",
        borderRadius: 8,
        padding: "8px 12px",
      }}
    >
      {tenants.map((t) => (
        <option key={t.id} value={t.id}>
          {t.name}
        </option>
      ))}
    </select>
  );
}
