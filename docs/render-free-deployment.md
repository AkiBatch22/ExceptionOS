# Deploy the ExceptionOS demo on Render for free

This setup creates three Render resources:

```text
Browser -> password-protected Next.js web service
                    -> API-key-protected FastAPI web service
                    -> Render PostgreSQL
```

Both web services are public because Render's free tier does not include a
private backend service. FastAPI rejects every non-health request unless it
contains the shared secret known only to the two services.

## 1. Push the prepared code

Render deploys from GitHub. Make sure these deployment changes are present in
the `main` branch of the ExceptionOS repository before continuing. Never commit
the local `.env` file.

## 2. Generate secrets

Run this PowerShell command four times and keep the four different results:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Use them as:

- `AUTH_SECRET`
- `API_SHARED_SECRET`
- `DEMO_RESET_SECRET`
- `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`

Create a separate strong `DEMO_PASSWORD` to give the founder. Do not reuse any
personal password.

## 3. Create PostgreSQL

1. Sign in to Render and select **New > Postgres**.
2. Name it `exceptionos-db`.
3. Select the region closest to the expected reviewer. Use the same region for
   both web services.
4. Choose the **Free** plan and create the database.
5. Open the database's **Connect** panel and copy its **Internal Database URL**.

The free database expires after 30 days and has no backups. Use only synthetic
or deidentified purchase orders.

## 4. Deploy FastAPI

1. Select **New > Web Service**.
2. Connect the GitHub repository and select its `main` branch.
3. Name the service `exceptionos-api`.
4. Select the same region as PostgreSQL.
5. Choose **Docker** and the **Free** instance type.
6. Leave **Root Directory** empty.
7. Set **Dockerfile Path** to `backend/Dockerfile`.
8. Set **Health Check Path** to `/ready`.
9. Add these environment variables:

```env
DATABASE_URL=<PostgreSQL Internal Database URL>
GROQ_API_KEY=<your Groq key>
GROQ_TIMEOUT_SECONDS=120
ENABLE_LLM_RECOMMENDATIONS=false
INBOX_POLL_INTERVAL_SECONDS=0
DEMO_MODE=true
DEMO_RETENTION_HOURS=48
DEMO_RESET_SECRET=<generated reset secret>
EXTRACTION_RATE_LIMIT_PER_MINUTE=20
API_SHARED_SECRET=<generated API shared secret>
```

Do not add `PORT`; Render supplies it. Create the service and wait for the log
to show that the migration completed and Uvicorn started. Copy the public URL,
for example `https://exceptionos-api.onrender.com`.

Opening `/health` should return `{"status":"ok"}`. Opening `/reviews` directly
should return `401 Unauthorized`.

## 5. Deploy Next.js

1. Select **New > Web Service** again.
2. Choose the same repository and `main` branch.
3. Name it `exceptionos-demo`.
4. Select the same region and the **Free** instance type.
5. Set **Root Directory** to `frontend`.
6. Choose **Docker**. The Dockerfile path is `Dockerfile` relative to that root.
7. Set **Health Check Path** to `/api/health`.
8. Add these environment variables:

```env
API_URL=https://exceptionos-api.onrender.com
API_SHARED_SECRET=<the exact same API shared secret>
DEMO_AUTH_ENABLED=true
AUTH_SECRET=<generated auth secret>
DEMO_USERNAME=trelium-demo
DEMO_PASSWORD=<your separate demo password>
DEMO_RESET_SECRET=<the exact same reset secret>
NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=<generated encryption key>
```

Create the service. Its `onrender.com` URL is the only URL to share.

## 6. Verify before sharing

1. Open the frontend URL in an incognito window.
2. Confirm that it redirects to `/login`.
3. Confirm that an incorrect password fails.
4. Sign in with `trelium-demo` and the configured password.
5. Upload one valid test PDF and verify that an ERP order is created.
6. Upload one exception PDF and verify that a pending review appears.
7. Open the FastAPI `/reviews` URL directly and confirm it returns `401`.
8. Test correction, approval, audit timing, and logout.

Free Render web services sleep after 15 minutes without traffic. Before a live
demo, open the backend `/health` URL, wait for it to wake, and then open the
frontend. A reviewer opening it later may see a cold-start delay. Do not use
external uptime services to bypass the free-tier idle policy.
