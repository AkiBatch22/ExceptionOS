# ExceptionOS architecture

## Purpose

ExceptionOS is a local, learning-focused purchase-order operations application. It accepts purchase orders from text, PDF files, exported email files, or an IMAP inbox; extracts structured data with an AI model; requires human correction before execution; runs deterministic business checks; and either creates an ERP order or sends the exception to a human-review queue.

The central design rule is that AI extracts information, while ordinary application code controls business actions.

## System overview

```text
Text / PDF / EML / IMAP inbox
              │
              ▼
     PDF text extraction
       or Tesseract OCR
              │
              ▼
 Groq structured extraction
              │
              ▼
 PostgreSQL imported draft
              │
              ▼
 Human correction in Next.js
              │
              ▼
 Deterministic assessment
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
ERP order         Human-review queue
                        │
                  approve / reject
                        │
                        ▼
                 ERP order or stop

Every processing decision writes audit events.
```

## Components

### Next.js frontend

The frontend provides an operations dashboard, ingestion controls, an editable extraction form, explicit assessment and processing actions, and review decision pages. Its server actions call FastAPI; it never connects directly to PostgreSQL, IMAP, Groq, or Tesseract.

### FastAPI backend

FastAPI validates requests and exposes ingestion, draft lifecycle, review, audit, liveness, and readiness endpoints. Pydantic defines the boundary between untrusted input and business logic. A structurally invalid order receives `422 Unprocessable Entity` before business logic runs.

### AI extraction

Groq runs `openai/gpt-oss-20b` with a strict JSON schema. The prompt requires the model to use only supplied values, return `null` for missing scalar fields, and list missing paths in `missing_fields`.

AI output is a draft. It cannot directly create an ERP order. A user can correct it before assessment and processing.

### Deterministic business logic

Normal Python functions check customer existence, SKU and inventory availability, and exact unit prices against reference ERP data. If every check passes, processing creates an ERP order. Any issue creates a pending human review instead. Approval creates the order; rejection records the decision without creating one.

### PostgreSQL

PostgreSQL stores state that must survive restarts:

- `erp_orders` stores created orders as validated JSONB;
- `reviews` stores pending and decided exceptions;
- `audit_events` stores ordered events for each PO number;
- `email_imports` stores inbox identifiers, extraction drafts, and lifecycle state.

The product catalog and customer reference list intentionally remain in memory. They represent a future ERP integration boundary rather than production ERP data.

## Ingestion paths

### Raw text

`POST /purchase-orders/extract` sends supplied text directly to structured AI extraction.

### PDF

`POST /purchase-orders/extract-pdf` first uses `pypdf`. Pages without selectable text use PyMuPDF and local Tesseract OCR at 300 DPI. The combined text enters the same AI extraction function.

### Exported email

`POST /purchase-orders/extract-email` parses an uploaded `.eml` file with Python's standard email package. Exactly one PDF attachment is required.

### IMAP inbox

`POST /purchase-orders/import-email` checks up to 20 unread messages. `BODY.PEEK[]` prevents fetching from marking messages as read. The first email containing exactly one PDF is extracted and stored as a draft.

Automatic polling runs the same import function when `INBOX_POLL_INTERVAL_SECONDS` is positive. The task starts and stops with FastAPI and performs blocking IMAP and AI work in a worker thread.

## Email idempotency

An inbox email is identified by `Message-ID`, or by a SHA-256 hash of its raw bytes when the header is absent. `email_imports.message_id` is the PostgreSQL primary key, and inserts use conflict-safe SQL.

Successful imports are recorded before the message is marked read. Failed extraction is not recorded and remains retryable. Previously imported unread messages are skipped and marked read rather than extracted again.

## Draft lifecycle

An imported draft starts as `pending`. The dashboard lists only pending drafts. The user corrects, assesses, and explicitly processes it through `POST /email-imports/process`.

The draft changes to `completed` only after processing creates either an ERP order or a human-review record. Completed drafts remain in PostgreSQL history and cannot be processed twice through the normal workflow.

## Audit trail

Processing writes events in insertion order:

- `purchase_order_received`;
- `review_created` when an exception exists;
- `review_approved` or `review_rejected` after a decision;
- `erp_order_created` when an order is created.

`GET /purchase-orders/{po_number}/events` returns this history.

## Operational behavior

- PDF and EML uploads are limited to 10 MB at the application layer.
- Groq and IMAP calls default to 30-second timeouts.
- `/health` confirms that FastAPI is alive.
- `/ready` checks PostgreSQL, required tables, and English Tesseract data.
- Polling is disabled by default and requires a positive interval.
- Tests use a separate database whose name ends in `_test`.

## API map

Purchase-order endpoints:

- `POST /purchase-orders/extract`
- `POST /purchase-orders/extract-pdf`
- `POST /purchase-orders/extract-email`
- `POST /purchase-orders/import-email`
- `POST /purchase-orders/validate`
- `POST /purchase-orders/check-customer`
- `POST /purchase-orders/check-inventory`
- `POST /purchase-orders/check-prices`
- `POST /purchase-orders/assess`
- `POST /purchase-orders/process`
- `GET /purchase-orders/{po_number}/events`

Imported-draft endpoints:

- `GET /email-imports`
- `GET /email-imports/detail?message_id=...`
- `POST /email-imports/process?message_id=...`

Review endpoints:

- `GET /reviews?status=pending`
- `GET /reviews/{review_id}`
- `POST /reviews/{review_id}/decision`

Operational endpoints:

- `GET /health`
- `GET /ready`

## Deliberate limitations

- There is no authentication or authorization.
- Catalog and customer reference data are static in-memory dictionaries.
- The ERP writer is local PostgreSQL code, not a commercial ERP API.
- Polling assumes one FastAPI process. Multiple workers could fetch the same message concurrently before deduplication completes.
- Workflow writes use small independent transactions rather than one distributed transaction.
- OCR is configured for English.
- Upload limits apply after multipart parsing; a public deployment should also enforce limits at a reverse proxy.
- There is no cloud deployment, notification service, or mailbox OAuth flow.

These constraints are intentional for a clear local teaching project.

## Why there is no LangGraph

The workflow is a short deterministic branch: extract, correct, assess, then create or review. Plain functions are easier to read, test, and explain. LangGraph would become useful for long-running resumable workflows, many tool-calling branches, checkpoints, or agent-directed retries. It would not improve the current behavior.
