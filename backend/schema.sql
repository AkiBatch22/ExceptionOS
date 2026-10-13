CREATE TABLE IF NOT EXISTS erp_orders (
    erp_order_id TEXT PRIMARY KEY,
    po_number TEXT UNIQUE NOT NULL,
    purchase_order JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    po_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    purchase_order JSONB NOT NULL,
    issues JSONB NOT NULL,
    erp_order_id TEXT REFERENCES erp_orders(erp_order_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    po_number TEXT NOT NULL,
    event TEXT NOT NULL,
    details JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS audit_events_po_number_id_idx
    ON audit_events (po_number, id);

CREATE TABLE IF NOT EXISTS email_imports (
    message_id TEXT PRIMARY KEY,
    imap_uid TEXT NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    attachment_name TEXT NOT NULL,
    po_number TEXT,
    extraction JSONB,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed')),
    completed_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE email_imports
    ADD COLUMN IF NOT EXISTS extraction JSONB;

ALTER TABLE email_imports
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending';

ALTER TABLE email_imports
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
