# Operator checklist

This checklist is the short handover path for updating knowledge or training data in
H.O.M AI Studio. It records provenance before the handoff, then verifies the platform
objects that make the update usable by founders and operators.

## Scope

Use this checklist when an operator uploads a new dataset, starts a training run,
registers a trained model version or hands a production/staging alias to a founder.

Do not use this checklist for unrelated UI-only changes. For deployment-only changes, use
the repository and live-site checks in the final section.

## 1. Source and provenance

Before upload or training, record:

- source owner and reviewer
- source repository, branch and commit SHA
- source file or export name
- intended dataset type and version label
- reason for the update

Minimum acceptance:

- the source SHA is immutable and reachable
- the reviewer is named
- the dataset name/version can be traced back to the source export
- no secret, token or private customer payload is copied into the handover text

## 2. Dataset gate

Upload through the API/UI so `apps/api` owns the database write and storage key.

Operator checks:

- dataset status is `ready`
- sample count is greater than zero
- validation errors are empty
- schema/stats are populated
- audit log contains `dataset_uploaded`

Stop if the dataset is `invalid`, empty or missing validation stats.

## 3. Training gate

Create the training job only from a `ready` dataset and a registered base model.

Operator checks:

- job starts from `queued`
- allowed state path follows `queued -> preparing -> running -> evaluating -> completed`
- failed or cancelled jobs are treated as terminal and are not reused
- logs include preparation, provider start and completion/failure context
- GPU/provider errors are reported as operator blockers, not hidden by a retry-only handoff

Stop if the worker reports `GPU_UNAVAILABLE`, missing LLaMA-Factory/vLLM tooling or an
invalid job transition.

## 4. Registry and alias gate

Register a model version only after a completed training job.

Operator checks:

- model version references the training job, dataset and base model
- training config and final metrics are present
- version status is intentional (`experimental`, `staging` or `production`)
- `hom-crm-staging` or `hom-crm-production` points to the intended model version
- audit log records model registration, alias/status changes or archival actions

Stop if the alias points to an older or unreviewed version.

## 5. Deployment and founder handoff

Before reporting a deployable/testable handoff:

- `git status --short --branch` is clean and synchronized with `origin/main`
- latest local SHA equals latest remote SHA
- `npm run lint` and `npm run build` pass in `apps/web` for frontend-impacting changes
- relevant backend/worker tests pass when API, dataset, training or registry behavior changes
- `https://hom-ai-studio.vercel.app/` returns HTTP 200
- `https://hom-ai-studio.vercel.app/deployment-smoke.json` returns `status: ok`,
  `repository: HDieter6789/hom_ai_studio` and `vercelProject: hom-ai-studio`

Founder handoff message should include:

- source SHA and dataset/version name
- training job ID or explicit reason no training job was started
- model version ID and alias, when applicable
- test/build commands and result
- live URL and HTTP result
- blockers in one sentence or `none`

## Minimal handoff template

```text
Source:
- repo/branch/SHA:
- reviewer:
- dataset/version:

Dataset:
- id:
- status:
- samples:
- validation errors:

Training:
- job id:
- terminal status:
- provider/GPU note:

Registry:
- model version:
- alias:

Verification:
- tests/build:
- live URL:
- smoke:
- blockers:
```
