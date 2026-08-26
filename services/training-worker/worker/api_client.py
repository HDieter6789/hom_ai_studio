"""Thin HTTP client the worker uses to talk to apps/api's internal
endpoints. The worker never opens a direct connection to Postgres -
apps/api is the single owner of persistent state (see architecture notes
in packages/hom_core)."""

import httpx

from worker.config import get_worker_settings


def _client() -> httpx.Client:
    settings = get_worker_settings()
    return httpx.Client(
        base_url=settings.api_base_url,
        headers={"X-Internal-Token": settings.internal_api_token},
        timeout=30,
    )


def get_training_job_config(job_id: str) -> dict:
    with _client() as client:
        resp = client.get(f"/api/internal/training-jobs/{job_id}/config")
        resp.raise_for_status()
        return resp.json()


def post_training_status(job_id: str, payload: dict) -> None:
    with _client() as client:
        resp = client.post(f"/api/internal/training-jobs/{job_id}/status", json=payload)
        resp.raise_for_status()


def post_training_log(job_id: str, level: str, message: str) -> None:
    with _client() as client:
        resp = client.post(f"/api/internal/training-jobs/{job_id}/logs", json={"level": level, "message": message})
        resp.raise_for_status()


def get_deployment_config(deployment_id: str) -> dict:
    with _client() as client:
        resp = client.get(f"/api/internal/deployments/{deployment_id}/config")
        resp.raise_for_status()
        return resp.json()


def post_deployment_status(deployment_id: str, payload: dict) -> None:
    with _client() as client:
        resp = client.post(f"/api/internal/deployments/{deployment_id}/status", json=payload)
        resp.raise_for_status()


def post_worker_heartbeat(payload: dict) -> None:
    with _client() as client:
        resp = client.post("/api/workers/heartbeat", json=payload)
        resp.raise_for_status()
