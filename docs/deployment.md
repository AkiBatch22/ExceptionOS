# Private demo deployment

This runbook deploys ExceptionOS as three services while exposing only the
password-protected Next.js frontend.

```text
Browser -> public Next.js service -> private FastAPI service -> private PostgreSQL
                                      |
                                      +-> Groq API
```

The deployment is intended for synthetic or deidentified demonstration data.
It is not a substitute for production SSO, tenant isolation, malware scanning,
or a formal data-processing agreement.

## Prepare secrets

Generate separate random values for `AUTH_SECRET`, `DEMO_PASSWORD`,
`DEMO_RESET_SECRET`, and `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`. On a current
PowerShell installation, this command produces a 32-byte base64 value:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Do not commit the generated values or paste them into a public issue.

## Backend variables

```env
PORT=8000
DATABASE_URL=<managed PostgreSQL internal URL>
GROQ_API_KEY=<secret>
GROQ_TIMEOUT_SECONDS=120
ENABLE_LLM_RECOMMENDATIONS=false
INBOX_POLL_INTERVAL_SECONDS=0
DEMO_MODE=true
DEMO_RETENTION_HOURS=48
DEMO_RESET_SECRET=<secret>
EXTRACTION_RATE_LIMIT_PER_MINUTE=20
```

Run `python -m backend.migrate` before each backend deployment. Use `/ready`
as the health-check path. The backend image installs Tesseract and English
language data, so both digital and scanned PDFs work.

## Frontend variables

```env
API_URL=<private FastAPI URL>
DEMO_AUTH_ENABLED=true
AUTH_SECRET=<at least 32 random characters>
DEMO_USERNAME=trelium-demo
DEMO_PASSWORD=<at least 12 random characters>
DEMO_RESET_SECRET=<same value configured on the backend>
NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=<stable 32-byte base64 key>
```

Only the frontend receives a public domain. The signed session cookie is
HTTP-only, secure in production, same-site, and expires after 12 hours. Login
failures are limited to five attempts per address per 15 minutes. Every page,
Server Action, and source-document route performs an authorization check.

## Railway

Create one project containing PostgreSQL plus two repository-backed services.

### Backend service

- Service name: `backend`
- Repository root: `/`
- Dockerfile: `backend/Dockerfile`
- Pre-deploy command: `python -m backend.migrate`
- Health check: `/ready`
- Port: `8000`
- Public domain: none
- `DATABASE_URL`: reference the PostgreSQL service's internal URL

### Frontend service

- Service name: `frontend`
- Repository root: `/frontend`
- Dockerfile: `Dockerfile` (or leave automatic detection enabled)
- Health check: `/api/health`
- Public domain: generate one
- `API_URL`: `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8000`

Test the public frontend URL in an incognito window. Direct access to FastAPI
should be impossible because the backend has no public domain.

## Render fallback

Create all resources in the same Render region.

1. Create Render PostgreSQL.
2. Create the backend as a **Private Service** from repository root `/` using `backend/Dockerfile`.
3. Set the backend pre-deploy command to `python -m backend.migrate`.
4. Create the frontend as a **Web Service** from root `/frontend` using `Dockerfile`.
5. Set `API_URL` to the backend address shown in Render's **Connect > Internal** panel.
6. Give only the frontend a public `onrender.com` or custom domain.

## Verification checklist

1. An incognito request is redirected to `/login`.
2. `GET /api/health` returns `200` without disclosing application data.
3. Incorrect credentials fail and repeated failures are throttled.
4. Correct credentials create a secure session and reveal the dashboard.
5. A digital PDF extracts successfully.
6. A scanned PDF exercises Tesseract OCR successfully.
7. A valid PO creates an ERP order.
8. A stock or price exception creates a pending review.
9. Correction, approval, rejection, source evidence, and audit history work.
10. `POST /demo/reset` is inaccessible without the secret and demo mode.
11. The dashboard reset requires the literal confirmation `RESET`.
12. Expired demo data is removed after the configured retention window.
13. Logging out removes the session.

## n8n

n8n is intentionally omitted from the first private deployment. If it is later
deployed inside the same platform project, update both HTTP Request nodes to use
the backend's private address. Do not expose FastAPI publicly only to support
n8n.
