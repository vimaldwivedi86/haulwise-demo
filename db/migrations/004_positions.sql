CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    speed_kmh DOUBLE PRECISION NOT NULL DEFAULT 0,
    heading DOUBLE PRECISION NOT NULL DEFAULT 0,
    ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_positions_vehicle_ts ON positions(vehicle_id, ts DESC);
CREATE INDEX idx_positions_tenant ON positions(tenant_id);
