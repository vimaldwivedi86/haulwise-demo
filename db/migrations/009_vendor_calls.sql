CREATE TABLE vendor_calls (
    id BIGSERIAL PRIMARY KEY,
    vendor TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    payload_preview JSONB,
    driver_id UUID REFERENCES drivers(id),
    ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_vendor_calls_ts ON vendor_calls(ts DESC);
