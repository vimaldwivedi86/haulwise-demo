CREATE TABLE video_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    driver_id UUID REFERENCES drivers(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    type TEXT NOT NULL, -- harsh_braking | lane_departure | face_mismatch | drowsiness
    severity TEXT NOT NULL DEFAULT 'medium', -- low | medium | high
    clip_key TEXT,
    face_snapshot_key TEXT,
    ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_video_events_vehicle_ts ON video_events(vehicle_id, ts DESC);
CREATE INDEX idx_video_events_driver ON video_events(driver_id);
