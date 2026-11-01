# Vercel frontend deployment

## What runs where

- **Vercel:** Next.js UI, read-only project-data APIs, and the authenticated streaming proxy at `POST /api/agents`.
- **Render:** GAIB-1 Python runtime, notebook artifacts, and calls to ThaiLLM, Cloudflare, Qdrant, and Jina.

The root [`render.yaml`](../../render.yaml) manages only the Render Python service. Vercel and Render deploy independently from the same Git repository.

## Deploy the frontend

1. Push the repository to GitHub, including `web/package-lock.json` and the generated `web/data/` snapshots.
2. In Vercel, import the repository and set **Root Directory** to `web`.
3. Keep the detected **Next.js** framework and default build settings. Vercel installs from `package-lock.json` and runs `npm run build`.
4. Add these environment variables to the Vercel project:

   | Variable | Value |
   |---|---|
   | `GAIB_RUNTIME_URL` | Render backend URL, e.g. `https://gold-assistant-gaib.onrender.com` |
   | `GAIB_SERVICE_TOKEN` | High-entropy shared token; must exactly match the Render backend value |

   Set them for Production and Preview only if those deployments should be able to call the production backend. Never expose the token with a `NEXT_PUBLIC_` prefix.

5. Deploy and wait for the build to finish.
6. In the Vercel project, open **Settings → Analytics** and enable Web Analytics. The app already includes the `<Analytics />` component; the Analytics dashboard is for page views/visitors and does not report Render or AI health.

## Data snapshots and API functions

`next.config.ts` uses `outputFileTracingIncludes` to package the required files from `web/data/` into the corresponding server functions:

- `/api` and `/api/data`: manifest
- `/api/data/market`: market history snapshot
- `/api/data/portfolios`: portfolio catalog
- `/api/data/portfolios/[portfolioId]`: manifest and yearly portfolio snapshots

These are read-only, versioned files; no application database or writable disk is required. Re-export and commit the snapshots when the source Parquet data intentionally changes.

## Verify the deployment

1. Open `https://<your-vercel-domain>/api`. Expect `status: "ok"` and `gaibRuntimeConfigured: true`.
2. Open `/api/data`, `/api/data/market?limit=5`, and `/api/data/portfolios?limit=5`. Confirm the endpoints return the expected snapshots.
3. Submit a non-sensitive question through Gold Assistant and confirm streamed agent events and the final citation-checked report appear.
4. If the AI request fails, check both deployments' logs and confirm `GAIB_RUNTIME_URL`, matching service tokens, and provider credentials. A missing backend configuration must remain an explicit error.
5. In **ถาม Gold Assistant**, use the Render status panel to check whether the backend is ready, starting/cold-starting, missing configuration, or unavailable. It retries a few times while starting and can be checked manually. A healthy `/health` confirms the Python process and shared token only; a real question is still needed to verify external AI providers and the complete pipeline.

The agent route allows up to 300 seconds per Vercel function invocation. If a request exceeds the maximum duration available to the Vercel plan, the function will time out; inspect actual request duration before raising the limit or changing plans.

## Security notes

- Keep all API keys and `GAIB_SERVICE_TOKEN` in platform environment settings, never in source or browser-visible variables.
- The browser calls the same-origin Next.js proxy; it does not receive the backend token.
- The Render backend remains directly reachable, but its agent endpoint requires the shared bearer token. Keep `/health` unauthenticated for platform health checks only.
