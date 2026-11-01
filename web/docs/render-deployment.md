# Render deployment

## Service

The root [`render.yaml`](../../render.yaml) creates one Render Web Service:

| Service | Runtime | Role |
|---|---|---|
| `gold-assistant-gaib` | Python | Imports the GAIB-1 Python pipeline modules and streams agent results |

The Python service is configured as a Standard instance because the pipeline loads a 19,784-chunk local BM25 corpus in memory. The Next.js frontend is deployed separately on Vercel; see the [Vercel Services guide](vercel-deployment.md). No PostgreSQL, Supabase, SQLite, or persistent Render disk is provisioned.

The runtime does use the remote Qdrant vector collection; that is required for the selected A2 retrieval pipeline. Cloudflare supplies embeddings, Jina reranks results, and ThaiLLM generates the five structured agent outputs. Qdrant is an external vector database, not an application database for web users.

## Data flow

1. The repository contains the Python serving module, source feature tables, HMM model bundle, simulator audit tables, and structure-aware RAG chunk corpus.
2. The Python service imports `web/python/gaib_pipeline.py` and reads the repository artifacts. The notebook is kept as a research/evaluation source and is never loaded or executed by the runtime.
3. `POST /api/agents` validates the question on Vercel and proxies it to the Python service using a private bearer token.
4. GAIB-1 retrieves evidence using Cloudflare embeddings + Qdrant dense search + local BM25/RRF + Jina reranking; it then computes market/HMM/risk evidence, runs agents 1–4, and asks the Lead Researcher to synthesize and audit citations.
5. The Python service streams structured agent outputs, validation state, source metadata, run metrics, and the final citation-checked report back through Next.js.

The web project-data APIs remain read-only, versioned exports. Portfolio simulator records are synthetic. The GAIB-1 Python service does not receive a portfolio ID selected in the web UI, so its risk audit is based on project-level simulator evidence and is not a personal account analysis. Market and news inputs are historical corpus/snapshots, not live feeds.

## Required Render secrets

Configure these only in the Render Environment tabs; never commit their values:

| Variable | Service | Purpose |
|---|---|---|
| `GAIB_SERVICE_TOKEN` | Render Python + Vercel frontend | Shared bearer token protecting the Python runtime endpoint |
| `THAILLM_API_KEY1`–`THAILLM_API_KEY7` | Python | OpenAI-compatible ThaiLLM agent calls; at least one key is required |
| `CLOUDFLARE_ACCOUNT_ID` | Python | Cloudflare embedding endpoint |
| `CLOUDFLARE_API_TOKEN` | Python | Cloudflare embedding endpoint |
| `QDRANT_URL` | Python | Remote Qdrant collection |
| `QDRANT_API_KEY` | Python | Remote Qdrant authentication |
| `JINA_API_KEY`, `JINA_API_KEY2`, `JINA_API_KEY3`, `JINA_API_KEY4` | Python | Required Jina reranking; at least one key is required |

Set `GAIB_RUNTIME_URL` on Vercel to the Python service's Render hostname, for example `https://gold-assistant-gaib.onrender.com`. Set the same high-entropy `GAIB_SERVICE_TOKEN` on both Vercel and Render. Do not configure Z AI credentials; the frontend no longer calls Z AI. The Python pipeline requires remote A2 retrieval, so missing credentials, unavailable providers, or invalid artifacts produce an explicit error and never trigger a fallback answer.

The Python endpoint is publicly addressable by Render but rejects requests without the shared token. `/health` is intentionally unauthenticated for Render health checks and does not report secret values.

## Deploy and verify

1. Push the repository, `web/package-lock.json`, and generated `web/data/` exports to the connected Git repository.
2. Create a Render Blueprint from the repository root and apply `render.yaml`. It creates only the Python `gold-assistant-gaib` service; deploy the frontend separately on Vercel.
3. In the `gold-assistant-gaib` Environment tab, add the ThaiLLM, Cloudflare, Qdrant, Jina, and `GAIB_SERVICE_TOKEN` secrets.
4. Confirm `GET https://gold-assistant-gaib.onrender.com/health` returns `status: ok` and `serviceAuthConfigured: true`.
5. In Vercel, set `GAIB_RUNTIME_URL` to the Render service URL and set the identical `GAIB_SERVICE_TOKEN`. See the [Vercel guide](vercel-deployment.md).
6. Submit a non-sensitive test question on the Vercel site. Confirm the stream shows `GAIB-1 Python · ThaiLLM`, agent schema states, citations, HMM/risk provenance, and a final report. A provider failure should appear as an error, not a successful-looking answer.
7. Verify `/api`, `/api/data`, market pagination, and a synthetic portfolio detail endpoint independently of the AI runtime.

## Operating limits

- The first question after a Python service restart imports the serving module, loads feature/model files and the chunk corpus, and connects to remote Qdrant; allow a cold-start delay.
- The runtime processes one question at a time to bound memory and ThaiLLM concurrency. Concurrent questions receive HTTP 429 and can be retried.
- The Python service must keep access to the repository artifacts at runtime. Do not move it to a Render root directory that excludes `embedding/`, `model/`, `dataset/`, or `multi_agent/`.
- Render restarts may clear process memory, but do not lose source data: all local inputs ship with the repository. No user data is written to the service filesystem.
- The GAIB-1 benchmark shown under project details is a development evaluation, not an accuracy guarantee for a live question or release approval.
