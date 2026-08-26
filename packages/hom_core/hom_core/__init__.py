"""Shared domain layer for H.O.M AI Studio.

This package is intentionally free of any framework or infrastructure
dependency (no FastAPI, no SQLAlchemy, no Celery). It defines the
vocabulary the rest of the system agrees on:

- enums for statuses/types shared across services
- Pydantic schemas for cross-service payloads (training config, job status, ...)
- abstract provider interfaces (TrainingProvider, InferenceProvider,
  ComputeProvider, StorageProvider) that concrete adapters implement

apps/api, services/training-worker and services/inference all depend on
this package, never on each other's internals.
"""
