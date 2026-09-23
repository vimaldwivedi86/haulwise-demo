CREATE TABLE dpr_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cmp_request_id TEXT NOT NULL,
    driver_id UUID NOT NULL REFERENCES drivers(id),
    trigger TEXT NOT NULL, -- e.g. consent.withdrawn:face_verification
    status TEXT NOT NULL DEFAULT 'open', -- open | closed
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE TABLE dpr_steps (
    id BIGSERIAL PRIMARY KEY,
    dpr_id UUID NOT NULL REFERENCES dpr_requests(id),
    step INT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending | done | failed
    evidence JSONB,
    ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dpr_steps_dpr ON dpr_steps(dpr_id, step);
