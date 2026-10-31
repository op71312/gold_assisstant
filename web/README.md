# Gold Assistant Web

## Run locally

Requires Node.js 20.9 or newer. From `web/`:

```powershell
bun install --frozen-lockfile
bun run dev
```

Open `http://localhost:3000`. To use npm, run `npm install` and then `npm run dev`, `npm run lint`, or `npm run build`.

The production build includes the static project data in `.next/standalone/data`. Start it with `bun run start` (or `npm start`).

## Versioned project data

The checked-in bundles under `data/` are deterministic, gzip-compressed JSON exports from the project Parquet tables (except the small, plain-text manifest):

- `market-history.json.gz`: 6,261 rows from `dataset/datset a gold price/data/processed/thai_gold_features_v1.parquet`.
- `portfolio-catalog.json.gz` and `portfolio-years/*.json.gz`: `portfolio_master`, `portfolio_valuation_monthly`, and `transaction_ledger` from simulator run `R_FEATURE_V1`.
- `manifest.json`: row counts, source paths, SHA-256 checksums, and data coverage.

Portfolio simulation rows are synthetic scenario outputs, **not real customer accounts or trades**. Missing market values remain `null`; the export does not interpolate, forward-fill, or otherwise impute prices. Re-export after intentionally updating the source Parquet files:

```powershell
..\.venv\Scripts\python.exe scripts\export_project_data.py
```

The export script requires pandas and a Parquet engine (the repository's `.venv` includes them). The Next.js service serves these versioned files without an application database or persistent disk.

Read-only APIs:

- `GET /api/data` — sources, coverage, row counts, and synthetic-data status.
- `GET /api/data/market?from=2026-01-01&to=2026-10-13&limit=100&offset=0&order=desc` — paginated rows from the feature table.
- `GET /api/data/portfolios?year=2025&limit=25&offset=0` — paginated synthetic portfolio catalog.
- `GET /api/data/portfolios/P20250001` — one portfolio's source master row, monthly valuations, and transaction ledger, including rejected orders.
- `GET /api` — Render health check.
- `POST /api/agents` — validates a question and streams the response from the Python GAIB-1 runtime. The runtime executes the selected code cells from `multi_agent/GAIB-1/Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb`; it does not use the former deterministic web-agent tools or fallback narration.

The web data APIs use static, versioned files and do not depend on PostgreSQL, SQLite, Supabase, or writable disk. GAIB-1 separately uses the notebook's remote Qdrant vector collection for retrieval; it also requires Cloudflare embeddings and Jina reranking. Portfolio simulator rows remain synthetic.
Open **ข้อมูลโครงการ** in the sidebar to browse the latest source-market rows, page through the synthetic portfolio catalog, and inspect a selected portfolio's ledger and valuation chart.

### Snapshot boundary

`data/market-history.json.gz` contains 6,261 feature rows through `2026-10-13`. The GAIB-1 runtime loads the notebook's source feature table, HMM bundle, simulator audit tables, and RAG corpus from the repository. These are historical/research inputs, not live market or news feeds. GAIB-1 does not receive the portfolio ID selected in the web data-table view, so its risk audit is project-level simulator evidence, not a personal portfolio diagnosis.

## Project research and documentation

The single **ข้อมูลโครงการ** page groups the project's dataset tables and research in tabs. Its research is summarized from the repository [research methodology](../docs/research-methodology.md) and [EDA notes](../md/eda.md):

- GTA price history → EDA/data-quality decisions → daily feature engineering → Gaussian HMM.
- Thai PBS/Fed/BLS evidence corpus → chunking and embedding evaluation → Qdrant → hybrid RAG.
- Embedding/RAG experiment metrics: five chunking strategies over 114 queries; hybrid + Jina evidence recall 52.6% versus 35.5% for hybrid RRF; prompt runs include citation, structured-output, and latency measures.
- GAIB-1 five-agent architecture, A2 hybrid retrieval, recorded development metrics, and the live web-to-notebook runtime boundary.
- Dataset sources and acquisition, return/correlation summaries, missing-data handling, HMM state profiles, and model limitations.

The EDA tab visualizes the recorded return correlations; the data-table tab charts valuations for a selected synthetic portfolio. Select a diagram node to inspect inputs, processing, measured outputs, selection rationale, and source evidence. The web `/api/agents` route now executes GAIB-1's notebook pipeline; the recorded `DEVELOPMENT_PASS` remains a development evaluation, not an accuracy score for an individual response or release approval because human review gates remain incomplete.

The **Gold Assistant** navigation opens the interactive question-and-answer workspace. Each question is sent to the GAIB-1 Python service, which runs the notebook's hybrid RAG, market/HMM/risk analysis, structured ThaiLLM agents, and citation audit. The UI streams agent results, schema status, citations, and the validated Lead Researcher report. A failed provider or missing secret is shown as an error; no deterministic answer is substituted.

## Render

The repository-root [`render.yaml`](../render.yaml) defines a Bun Next.js service and a Python GAIB-1 service. The Python service reads notebook artifacts from the checked-out repository and needs no persistent disk, but it does require a remote Qdrant collection plus private ThaiLLM, Cloudflare, Jina, and shared-service-token secrets. Set the same `GAIB_SERVICE_TOKEN` on both Render services. The Python worker is configured as a Standard instance because it loads the 19,784-chunk local BM25 corpus in memory. See [`docs/render-deployment.md`](docs/render-deployment.md) for service configuration, secrets, and operational limits.
