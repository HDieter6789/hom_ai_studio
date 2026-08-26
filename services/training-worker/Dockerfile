FROM python:3.11-slim

WORKDIR /srv

# System deps kept minimal on purpose: torch/transformers/LLaMA-Factory are
# intentionally NOT baked into this base image (huge, GPU-specific wheels).
# See services/training-worker/README.md for how to build a GPU-enabled
# image; this image already runs fully offline and reports "GPU
# unavailable" cleanly when those packages/drivers are absent.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY packages/hom_core /srv/packages/hom_core
COPY services/inference /srv/services/inference
COPY services/training-worker/requirements.txt /srv/services/training-worker/requirements.txt

WORKDIR /srv/services/training-worker
RUN pip install --no-cache-dir -r requirements.txt

COPY services/training-worker /srv/services/training-worker

ENV PYTHONUNBUFFERED=1
CMD ["celery", "-A", "worker.celery_app", "worker", "--beat", "--loglevel=INFO", "--concurrency=2"]
