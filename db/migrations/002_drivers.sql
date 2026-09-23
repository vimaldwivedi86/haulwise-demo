CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    dl_number TEXT NOT NULL,
    face_image_key TEXT,
    face_embedding TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_drivers_tenant ON drivers(tenant_id);
