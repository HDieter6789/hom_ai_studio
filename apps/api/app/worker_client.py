"""Producer-side handle to the job queue.

apps/api never imports services/training-worker's code (that would couple
the API to a specific trainer implementation). It only knows Celery task
*names* and the broker URL - the worker process registers the matching
task implementations independently.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("hom_api_producer", broker=settings.redis_url, backend=settings.redis_url)


def enqueue_training_job(job_id: str) -> None:
    celery_app.send_task("worker.tasks.run_training_job", args=[job_id], task_id=f"training-{job_id}")


def enqueue_cancel_training_job(job_id: str) -> None:
    celery_app.control.revoke(f"training-{job_id}", terminate=False)
    celery_app.send_task("worker.tasks.cancel_training_job", args=[job_id])


def enqueue_deployment(deployment_id: str) -> None:
    celery_app.send_task("worker.tasks.run_deployment", args=[deployment_id], task_id=f"deploy-{deployment_id}")


def enqueue_stop_deployment(deployment_id: str) -> None:
    celery_app.send_task("worker.tasks.stop_deployment", args=[deployment_id])
