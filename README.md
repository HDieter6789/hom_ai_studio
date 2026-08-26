# H.O.M AI Studio

A self-hosted platform for configuring, training, evaluating, versioning and deploying
specialized LLMs for CRM/agent use cases — no dependency on Azure ML, SageMaker, Vertex AI
or any other proprietary ML platform. The long-term target model is **HOM-CRM**: a model
fine-tuned for CRM data structures, tool calling, structured JSON output and multi-step
agent workflows.

## Architecture

```text
Browser
   │
   ▼
Next.js Frontend (apps/web)
   │  REST (JWT bearer)
   ▼
FastAPI Backend (apps/api)  ── owns Postgres, the only service that touches it
   │            │
   │            ▼
   │        PostgreSQL
   │
   ▼  Celery (Redis broker)
Training Worker (services/training-worker)
   │
   ▼
TrainingProvider interface ── LlamaFactoryTrainingProvider ── LLaMA-Factory ── GPU
   │
   ▼
Model Artifacts (shared storage volume) ── Model Registry (Postgres, owned by apps/api)
   │
   ▼
InferenceProvider interface ── VLLMInferenceProvider ── vLLM ── OpenAI-compatible API
   │
   ▼
Agents (any OpenAI-compatible client), fronted by a stable model alias
(hom-crm-production / hom-crm-staging / hom-crm-latest)
```

**Why apps/api owns Postgres exclusively:** services/training-worker and services/inference
never open a database connection. They call small internal HTTP endpoints
(`/api/internal/...`, gated by a shared secret, see `HOM_INTERNAL_API_TOKEN`) to fetch the
config they need and report status/logs/metrics back. This keeps persistence in one place
and means neither worker service can corrupt state by disagreeing with the API about schema.

### Provider abstraction (the part that matters most)

Nothing outside `packages/hom_core/hom_core/providers/*.py` may depend on a concrete
trainer, inference engine, storage backend or compute location:

```text
TrainingProvider    → LlamaFactoryTrainingProvider today, AxolotlTrainingProvider later
InferenceProvider   → VLLMInferenceProvider today
StorageProvider     → LocalStorageProvider today, S3/MinIO-backed later
ComputeProvider     → LocalGPUProvider / RemoteGPUProvider
```

Swapping LLaMA-Factory for a different trainer means writing a new class that implements
`TrainingProvider` in `services/training-worker/worker/providers/` — nothing in `apps/api`
or the frontend changes.

## Repository layout

```text
apps/
  api/            FastAPI backend — REST API, Postgres models/migrations, business logic
  web/            Next.js frontend
services/
  training-worker/  Celery worker: LLaMA-Factory adapter, GPU detection, job execution
  inference/        vLLM adapter (imported by training-worker; also independently testable)
packages/
  hom_core/       Shared, framework-free domain layer: enums, Pydantic schemas, provider
                   interfaces, local storage implementation
infrastructure/
  docker/          Dockerfiles for the api and web images
  scripts/         Container entrypoint / wait-for-postgres helpers
docs/
docker-compose.yml
.env.example
```

## Quick start (Docker Compose)

```bash
cp .env.example .env       # adjust secrets for anything beyond local dev
docker compose up --build
```

This starts Postgres, Redis, the backend (runs Alembic migrations automatically, then seeds
demo data because `HOM_SEED_ON_START=true` by default), the training worker, and the
frontend.

- Frontend: http://localhost:3000
- Backend API + OpenAPI docs: http://localhost:8000/docs
- Seeded logins: `admin@hom.local` / `changeme` (admin), `ml@hom.local` / `changeme` (ML engineer)

The training worker starts fine without a GPU — it reports **"GPU unavailable"** on the
Infrastructure page and fails any training job started against it with a clear
`GPU_UNAVAILABLE` error (not a crash) until a real GPU/driver is present.

## Development (without Docker)

### Backend

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../../.env.example ../../.env   # or export HOM_* vars directly

# Requires a running Postgres reachable at HOM_DATABASE_URL
alembic upgrade head
python -m app.seed        # optional demo data
uvicorn app.main:app --reload
```

Run tests:

```bash
cd apps/api
pytest   # uses an in-memory SQLite database, no external services required
```

### Training worker

```bash
cd services/training-worker
pip install -r requirements.txt
# Requires HOM_REDIS_URL and HOM_API_BASE_URL/HOM_INTERNAL_API_TOKEN pointing at a running API
celery -A worker.celery_app worker --beat --loglevel=INFO
pytest   # exercises the LLaMA-Factory adapter's config generation without invoking the CLI
```

### Inference adapter

```bash
cd services/inference
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

## Database & migrations

Postgres schema is managed with Alembic (`apps/api/alembic/`). The initial schema lives in
`apps/api/alembic/versions/0001_initial.py`. After changing a SQLAlchemy model, generate a
new migration:

```bash
cd apps/api
alembic revision --autogenerate -m "describe the change"
```

## GPU setup

The training worker auto-detects GPUs via `nvidia-smi` (see
`services/training-worker/worker/gpu.py`) — no GPU/driver present simply means
`ComputeProvider.is_available()` returns `False` and the Infrastructure page shows the
worker as online with zero GPUs, rather than the process crashing. To attach real GPUs under
Docker Compose, install the NVIDIA Container Toolkit on the host and uncomment the `deploy:`
block for the `training-worker` service in `docker-compose.yml`.

For a **remote** GPU box that's only powered on for the duration of a run, set
`HOM_COMPUTE_PROVIDER=remote` and `HOM_REMOTE_GPU_AGENT_URL` on the training-worker service —
`RemoteGPUProvider` (`services/training-worker/worker/providers/compute_remote.py`) polls
that agent's `/gpus` endpoint and degrades to "unavailable" if the box is offline, instead of
erroring.

## LLaMA-Factory

`services/training-worker/worker/providers/llama_factory.py` is the only file that knows
LLaMA-Factory's config format. It is **not** vendored into this repo (large, GPU-specific).
To run real training jobs:

```bash
git clone https://github.com/hiyouga/LLaMA-Factory services/training-worker/vendor/LLaMA-Factory
pip install -e services/training-worker/vendor/LLaMA-Factory
```

and point `HOM_LLAMA_FACTORY_REPO` at that path. Until then, starting a training job fails
fast with a `PROVIDER_ERROR` explaining that `llamafactory-cli` was not found — the platform
itself stays fully usable (dataset management, model registry, UI) without it.

## vLLM

`services/inference/inference/vllm_provider.py` shells out to `vllm serve` and tracks
deployments (pid, allocated port) in a small JSON registry file on the shared storage
volume, so deployments survive a worker restart being correctly reported as unhealthy rather
than the platform losing track of them. Install vLLM in the training-worker image (or a
dedicated GPU-enabled image) to serve real models:

```bash
pip install vllm
```

Without it, `POST /api/deployments` fails with a clear "vLLM not installed" error.

## Environment variables

See `.env.example` for the full list. Notable ones:

| Variable | Used by | Purpose |
|---|---|---|
| `HOM_DATABASE_URL` | api | Postgres connection string |
| `HOM_REDIS_URL` | api, training-worker | Celery broker/result backend |
| `HOM_SECRET_KEY` | api | JWT signing secret — **change for anything beyond local dev** |
| `HOM_INTERNAL_API_TOKEN` | api, training-worker | Shared secret for worker → API status callbacks |
| `HOM_STORAGE_ROOT` | api, training-worker | Shared volume root for datasets/artifacts/logs |
| `HOM_MAX_UPLOAD_SIZE_MB` | api | Dataset upload size limit |
| `HOM_COMPUTE_PROVIDER` | training-worker | `local` or `remote` |
| `NEXT_PUBLIC_API_BASE_URL` | web | Where the frontend reaches the backend |

## Security notes

- No secrets are hardcoded; every credential comes from environment variables (`.env`,
  never committed — see `.gitignore`).
- Dataset uploads are restricted to `.json`/`.jsonl`/`.csv`, size-capped
  (`HOM_MAX_UPLOAD_SIZE_MB`), and stored under a validated, namespaced key — user input can
  never escape the configured storage root (`LocalStorageProvider._resolve`,
  `packages/hom_core/hom_core/storage/local.py`).
- Every subprocess invocation (`nvidia-smi`, `llamafactory-cli`, `vllm serve`) uses a fixed
  argument list with `shell=False` — no user input is ever interpolated into a shell command.
- Authentication is JWT-bearer (`app/security.py`); RBAC is enforced per-endpoint via
  `require_role(...)` against four roles: `admin`, `ml_engineer`, `developer`, `viewer`.
- Critical actions are written to an append-only audit log (`GET /api/audit`, admin-only):
  training started/cancelled, model registered/deployed/archived, dataset
  uploaded/deleted, configuration changed.

## API

Full interactive documentation (OpenAPI/Swagger) is served at `/docs` by the running
backend. Key resource groups: `/api/auth`, `/api/datasets`, `/api/models`,
`/api/training/jobs`, `/api/evaluations`, `/api/registry` (+ `/api/registry/aliases`),
`/api/deployments`, `/api/workers`, `/api/audit`, `/api/overview`. `/api/internal/*` is
reserved for worker→API callbacks and requires the internal service token, not a user JWT.

## Known limitations / next steps

- This environment had no local Python/Docker toolchain available to execute the test
  suites or build the containers end-to-end — the code was written and carefully reviewed,
  but you should run `pytest` in each of `apps/api`, `services/training-worker` and
  `services/inference`, and `docker compose up --build`, as the first thing after cloning.
- Real SSO/OAuth is out of scope; `app/security.py` implements a minimal JWT flow that is
  the seam to swap in a real identity provider later.
- `RemoteGPUProvider` defines the contract for a remote GPU agent (`GET {agent_url}/gpus`)
  but does not ship that agent — only the platform side of the interface.
