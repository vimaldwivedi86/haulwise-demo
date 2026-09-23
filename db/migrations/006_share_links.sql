CREATE TABLE share_links (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_share_links_token ON share_links(token);
