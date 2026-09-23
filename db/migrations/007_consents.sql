CREATE TABLE consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    purpose TEXT NOT NULL, -- trip_tracking | safety_video | face_verification
    status TEXT NOT NULL,  -- granted | withdrawn
    receipt_id TEXT,
    ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_consents_driver_purpose ON consents(driver_id, purpose, ts DESC);
