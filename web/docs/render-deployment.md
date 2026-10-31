# Render deployment

## Service layout

The root [`render.yaml`](../../render.yaml) creates two Render Web Services:

| Service | Runtime | Role |
|---|---|---|
| `gold-assistant` | Bun | Next.js UI, static project-data APIs, and authenticated SSE proxy |
| `gold-assistant-gaib` | Python | Executes the GAIB-1 notebook pipeline and streams agent results |

The Python service is configured as a Standard instance because the notebook loads a 19,784-chunk local BM25 corpus in memory. The web service can remain on the Free plan. No PostgreSQL, Supabase, SQLite, or persistent Render disk is provisioned.

The runtime does use the notebook's remote Qdrant vector collection; that is required for the selected A2 retrieval pipeline. Cloudflare supplies embeddings, Jina reranks results, and ThaiLLM generates the five structured agent outputs. Qdrant is an external vector database, not an application database for web users.

## Data flow

1. The repository contains the notebook, source feature tables, HMM model bundle, simulator audit tables, and structure-aware RAG chunk corpus.
2. The Python service loads the notebook's runtime cells and those repository artifacts. It does not execute the benchmark/demo cells.
3. `POST /api/agents` validates the question in Next.js and proxies it to the Python service using a private bearer token.
4. GAIB-1 retrieves evidence using Cloudflare embeddings + Qdrant dense search + local BM25/RRF + Jina reranking; it then computes market/HMM/risk evidence, runs agents 1–4, and asks the Lead Researcher to synthesize and audit citations.
5. The Python service streams structured agent outputs, validation state, source metadata, run metrics, and the final citation-checked report back through Next.js.

The web project-data APIs remain read-only, versioned exports. Portfolio simulator records are synthetic. The GAIB-1 notebook does not receive a portfolio ID selected in the web UI, so its risk audit is based on project-level simulator evidence and is not a personal account analysis. Market and news inputs are historical corpus/snapshots, not live feeds.

## Required Render secrets

Configure these only in the Render Environment tabs; never commit their values:

| Variable | Service | Purpose |
|---|---|---|
| `GAIB_SERVICE_TOKEN` | Both services | Shared bearer token protecting the Python runtime endpoint |
| `THAILLM_API_KEY1`–`THAILLM_API_KEY7` | Python | OpenAI-compatible ThaiLLM agent calls; at least one key is required |
| `CLOUDFLARE_ACCOUNT_ID` | Python | Cloudflare embedding endpoint |
| `CLOUDFLARE_API_TOKEN` | Python | Cloudflare embedding endpoint |
| `QDRANT_URL` | Python | Remote Qdrant collection |
| `QDRANT_API_KEY` | Python | Remote Qdrant authentication |
| `JINA_API_KEY`, `JINA_API_KEY2`, `JINA_API_KEY3`, `JINA_API_KEY4` | Python | Required Jina reranking; at least one key is required |

The Blueprint sets `GAIB_RUNTIME_URL` to the Python service's Render hostname. Do not configure Z AI credentials; the web runtime no longer calls Z AI. The notebook requires remote A2 retrieval, so missing credentials, unavailable providers, or invalid notebook artifacts produce an explicit error and never trigger a fallback answer.

The Python endpoint is publicly addressable by Render but rejects requests without the shared token. Use a randomly generated, high-entropy token and set the exact same value on both services. `/health` is intentionally unauthenticated for Render health checks and does not report secret values.

## Deploy and verify

1. Push the repository and generated `web/data/` exports to the connected Git repository.
2. Create a Render Blueprint from the repository root and apply `render.yaml`.
3. In the `gold-assistant-gaib` Environment tab, add the ThaiLLM, Cloudflare, Qdrant, Jina, and `GAIB_SERVICE_TOKEN` secrets.
4. Add the same `GAIB_SERVICE_TOKEN` to the `gold-assistant` web service. Confirm `GAIB_RUNTIME_URL` points to the Python service.
5. Wait for both health checks. `GET /health` checks the Python process; `GET /api` reports whether the web proxy settings are present.
6. Submit a non-sensitive test question. Confirm the stream shows `GAIB-1 notebook · ThaiLLM`, agent schema states, citations, HMM/risk provenance, and a final report. A provider failure should appear as an error, not a successful-looking answer.
7. Verify `/api/data`, market pagination, and a synthetic portfolio detail endpoint independently of the AI runtime.

## Operating limits

- The first question after a Python service restart loads notebook code, feature/model files, the chunk corpus, and remote Qdrant state; allow a cold-start delay.
- The runtime processes one question at a time to bound memory and ThaiLLM concurrency. Concurrent questions receive HTTP 429 and can be retried.
- The Python service must keep access to the repository artifacts at runtime. Do not move it to a Render root directory that excludes `embedding/`, `model/`, `dataset/`, or `multi_agent/`.
- Render restarts may clear process memory, but do not lose source data: all local inputs ship with the repository. No user data is written to the service filesystem.
- The GAIB-1 benchmark shown under project details is a development evaluation, not an accuracy guarantee for a live question or release approval.
