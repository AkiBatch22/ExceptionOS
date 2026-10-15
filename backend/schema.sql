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

CREATE TABLE IF NOT EXISTS source_documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content BYTEA NOT NULL,
    page_texts JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_lookups (
    document_id TEXT NOT NULL REFERENCES source_documents(document_id)
        ON DELETE CASCADE,
    field_path TEXT NOT NULL,
    field_value TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT '',
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (document_id, field_path, field_value, context)
);

ALTER TABLE reviews
    ADD COLUMN IF NOT EXISTS source_document_id TEXT
        REFERENCES source_documents(document_id);

ALTER TABLE reviews
    ADD COLUMN IF NOT EXISTS recommendations JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS correction_patterns (
    id BIGSERIAL PRIMARY KEY,
    party_key TEXT NOT NULL,
    party_label TEXT NOT NULL,
    field_path TEXT NOT NULL,
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'suggestion_only'
        CHECK (status IN ('suggestion_only', 'trusted_suggestion', 'disabled')),
    confirmation_count INTEGER NOT NULL DEFAULT 1,
    rejection_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (party_key, field_path, original_value, corrected_value)
);

CREATE TABLE IF NOT EXISTS review_corrections (
    id BIGSERIAL PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    party_key TEXT NOT NULL,
    field_path TEXT NOT NULL,
    original_value TEXT,
    corrected_value TEXT NOT NULL,
    remembered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
