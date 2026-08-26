from celery import Celery

from worker.config import get_worker_settings

settings = get_worker_settings()

celery_app = Celery("hom_training_worker", broker=settings.redis_url, backend=settings.redis_url, include=["worker.tasks"])

celery_app.conf.update(
    task_track_started=True,
    worker_send_task_events=True,
    beat_schedule={
        "gpu-worker-heartbeat": {
            "task": "worker.tasks.send_heartbeat",
            "schedule": settings.heartbeat_interval_seconds,
        },
    },
)
