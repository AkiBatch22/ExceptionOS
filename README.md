# ExceptionOS

ExceptionOS is a learning-focused, full-stack purchase-order operations application. It ingests text, PDFs, scanned documents, exported emails, and IMAP inbox messages; extracts structured data with Groq; applies deterministic ERP checks; sends exceptions to human review; and records workflow state in PostgreSQL.

The key design boundary is simple:

```text
AI extracts information.
Deterministic application code controls business execution.
```

## What it demonstrates

- FastAPI and Pydantic request validation
- Next.js and React operator workflows
- Groq structured output with `openai/gpt-oss-20b`
- PDF text extraction and local Tesseract OCR fallback
- EML parsing and manual or automatic IMAP ingestion
- PostgreSQL persistence, audit history, and email deduplication
- deterministic customer, inventory, and price checks
- human-review approval and rejection
- imported-draft lifecycle management
- liveness, readiness, limits, timeouts, and end-to-end tests

## Workflow

```text
Email / PDF / text
        ↓
Text extraction or OCR
        ↓
Groq structured extraction
        ↓
Human correction
        ↓
Deterministic assessment
   ┌────┴────┐
   ↓         ↓
ERP order   Human review
```

## Documentation

- [Architecture](docs/architecture.md) — components, data flow, tables, endpoints, reliability, and limitations
- [Setup and runbook](docs/setup.md) — installation, configuration, startup, testing, and troubleshooting

## Quick start

Create the backend environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Copy `.env.example` to `.env`, then configure at minimum:

```env
GROQ_API_KEY=your-key
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/exceptionos
```

Initialize PostgreSQL and start FastAPI:

```powershell
.\.venv\Scripts\python.exe -m backend.init_db
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Install and start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. FastAPI exposes interactive API documentation at `http://127.0.0.1:8000/docs`.

For OCR and IMAP details, follow the [setup guide](docs/setup.md).

## n8n workflow

The repository includes an optional n8n workflow at
[`n8n/workflows/exceptionos-pdf-purchase-order-intake.json`](n8n/workflows/exceptionos-pdf-purchase-order-intake.json).
It accepts a PDF through an n8n form, calls ExceptionOS to extract and process the purchase order, and routes the response to either **Order Created** or **Human Review Required**.

To use it:

1. Start PostgreSQL, FastAPI, and n8n.
2. In n8n, create or open a workspace and choose **Import from File**.
3. Select `n8n/workflows/exceptionos-pdf-purchase-order-intake.json` from this repository.
4. Open the imported workflow and execute it manually to use the form's test URL, or activate it to use the production URL.
5. Upload a purchase-order PDF through the generated n8n form.

The two HTTP Request nodes call `http://127.0.0.1:8000`, which works when n8n and FastAPI run directly on the same machine. If n8n runs in Docker while FastAPI runs on the host, change both URLs to `http://host.docker.internal:8000` before running the workflow.

The exported workflow contains no credentials or API keys. Groq and PostgreSQL configuration remains in the local `.env` file used by ExceptionOS.

## Verification

Run backend tests from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Build the frontend:

```powershell
cd frontend
npm run build
```

Check the running backend:

- `GET /health` confirms process liveness.
- `GET /ready` confirms PostgreSQL schema and OCR readiness.

The backend suite includes complete success and human-review workflows. IMAP and Groq are mocked at their external boundaries; routes, generated PDF parsing, PostgreSQL state, deterministic processing, lifecycle transitions, and audit events run normally.

## Project status

The planned 30-stage local MVP is complete.

Deliberate non-goals include authentication, cloud deployment, a commercial ERP connection, distributed workers, and LangGraph. These are documented extension points rather than missing requirements.
