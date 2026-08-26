# Architecture notes

See the top-level [README](../README.md) for the full system diagram, repository layout and
setup instructions. This file covers two things not detailed there: the training job state
machine and the data model.

## Training job state machine

Enforced centrally in `hom_core.enums.TRAINING_JOB_TRANSITIONS` and applied by
`apps/api/app/services/training_service.apply_status_transition`. Both `apps/api` (on
cancel) and `services/training-worker` (via the `/api/internal/training-jobs/{id}/status`
callback) go through this single function, so an invalid transition is rejected in exactly
one place regardless of caller.

```text
QUEUED ──► PREPARING ──► RUNNING ──► EVALUATING ──► COMPLETED
   │            │            │            │
   └──► CANCELLED / FAILED ◄─┴────────────┘
```

`COMPLETED`, `FAILED` and `CANCELLED` are terminal — no further transition is accepted from
any of them.

## Data model (Postgres, owned exclusively by apps/api)

```text
users            — auth + RBAC role
base_models      — dynamically registered foundation models (never hardcoded)
datasets         — uploaded training data + computed validation stats
training_jobs    — one row per training run; training_logs holds its streamed log lines
model_versions   — the Model Registry; one row per trained, versioned model
model_aliases    — stable name → model_version_id pointers (hom-crm-production, ...)
evaluations      — evaluation runs against a model_version
deployments      — vLLM deployments of a model_version
workers          — GPU workers, registered dynamically via heartbeat
audit_logs       — append-only record of sensitive actions
```

Foreign keys: `training_jobs.base_model_id/dataset_id`, `model_versions.base_model_id/
dataset_id/training_job_id`, `model_aliases.model_version_id`, `evaluations.
model_version_id`, `deployments.model_version_id` all reference the tables above.
