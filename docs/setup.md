# ExceptionOS setup and runbook

## Prerequisites

Install Python 3.11 or newer, Node.js with npm, PostgreSQL, and Tesseract OCR with English language data.

On Windows, install Tesseract with:

```powershell
winget install --id tesseract-ocr.tesseract --exact
```

PostgreSQL's usual administrator username is `postgres`, not `root`.

## 1. Configure the backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Copy `.env.example` to `.env`, then replace placeholders:

```env
GROQ_API_KEY=your-groq-key
GROQ_TIMEOUT_SECONDS=30
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/exceptionos
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USERNAME=orders@example.com
IMAP_PASSWORD=your-app-password
IMAP_MAILBOX=INBOX
IMAP_TIMEOUT_SECONDS=30
INBOX_POLL_INTERVAL_SECONDS=0
```

Never commit `.env`. If a database password contains `@`, `:`, `/`, `#`, or `%`, URL-encode it in `DATABASE_URL`.

IMAP settings are optional unless inbox features are used. Many providers require an app password. Set `INBOX_POLL_INTERVAL_SECONDS=60` to poll every minute; keep it at `0` for manual-only imports.

If Tesseract uses a nonstandard location, set `TESSDATA_PREFIX` to the directory containing `eng.traineddata`.

## 2. Initialize PostgreSQL

```powershell
.\.venv\Scripts\python.exe -m backend.init_db
```

The initializer reads `DATABASE_URL`, creates the configured database when missing, and applies `backend/schema.sql`. The PostgreSQL user must have database-creation permission. Re-running the initializer is safe for the current additive schema.

## 3. Start FastAPI

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Useful URLs:

- `http://127.0.0.1:8000/health` — process liveness;
- `http://127.0.0.1:8000/ready` — database schema and OCR readiness;
- `http://127.0.0.1:8000/docs` — interactive API documentation.

## 4. Start Next.js

In a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Set the server-side `API_URL` environment variable if FastAPI does not use `http://127.0.0.1:8000`.

## 5. Exercise the workflow

1. Open **Extract a purchase order**.
2. Check the inbox, upload `.eml` or PDF, or paste text.
3. Review and correct extracted fields.
4. Assess the order.
5. Process the order explicitly.
6. If an exception exists, open its review and approve or reject it.
7. Inspect `/purchase-orders/{po_number}/events` for audit history.

Files must be no larger than 10 MB. An email must contain exactly one non-empty PDF attachment.

## 6. Test and build

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests use a separate database ending in `_test` and truncate only that database. The PostgreSQL account needs database-creation permission.

The end-to-end tests mock only IMAP and Groq. Routes, generated PDF parsing, PostgreSQL, deterministic decisions, lifecycle changes, and audit events run normally.

Build the frontend:

```powershell
cd frontend
npm run build
```

## Troubleshooting

### Database does not exist

Run `python -m backend.init_db` through the project virtual environment. Confirm that `DATABASE_URL` contains the intended database and that its user can create databases.

### PostgreSQL password authentication fails

Verify the password with `psql`. PostgreSQL passwords cannot be displayed; a forgotten password must be reset.

### `/ready` reports database unavailable

Check that PostgreSQL is running, `DATABASE_URL` is correct, and database initialization completed.

### `/ready` reports OCR unavailable

Confirm that `eng.traineddata` exists under Tesseract's `tessdata` directory. Set `TESSDATA_PREFIX` for a nonstandard installation.

### Groq extraction returns `503`

Confirm `GROQ_API_KEY`, network access, and a positive `GROQ_TIMEOUT_SECONDS`.

### Inbox import returns `503`

Check the IMAP host, port, username, app password, and provider settings. The port must be 1–65535 and the timeout positive.

### Inbox finds no message

Only unread messages with exactly one PDF qualify. Previously imported messages are deduplicated by `Message-ID` or content hash.

### OCR finds no text

Low-resolution, rotated, handwritten, or damaged scans can still fail. Confirm English is the correct OCR language and try a clearer scan.

### Windows `psql` code-page warning

The code page 437 versus 1252 message is an encoding warning, not an authentication result. A successful login displays a prompt such as `postgres=#`.
