from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.dataset import Dataset
from app.models.deployment import Deployment
from app.models.registry import ModelVersion
from app.models.training import TrainingJob
from app.models.user import User
from app.models.worker import Worker
from app.schemas.overview import OverviewResponse, OverviewStats
from hom_core.enums import DeploymentStatus, ModelVersionStatus, TrainingJobStatus, WorkerStatus

router = APIRouter(prefix="/api/overview", tags=["overview"])

_ACTIVE_JOB_STATUSES = (
    TrainingJobStatus.QUEUED,
    TrainingJobStatus.PREPARING,
    TrainingJobStatus.RUNNING,
    TrainingJobStatus.EVALUATING,
)


@router.get("", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    models_total = db.query(func.count(ModelVersion.id)).scalar() or 0
    production_models_count = (
        db.query(func.count(ModelVersion.id)).filter(ModelVersion.status == ModelVersionStatus.PRODUCTION).scalar()
        or 0
    )
    active_jobs = db.query(func.count(TrainingJob.id)).filter(TrainingJob.status.in_(_ACTIVE_JOB_STATUSES)).scalar() or 0
    jobs_30d = db.query(func.count(TrainingJob.id)).filter(TrainingJob.created_at >= thirty_days_ago).scalar() or 0
    datasets_total = db.query(func.count(Dataset.id)).scalar() or 0
    training_samples_total = db.query(func.coalesce(func.sum(Dataset.sample_count), 0)).scalar() or 0

    workers = db.query(Worker).all()
    gpu_workers_online = sum(1 for w in workers if w.status == WorkerStatus.ONLINE)
    utilizations = [g.get("utilization_pct") for w in workers for g in (w.gpus or []) if g.get("utilization_pct") is not None]
    avg_util = sum(utilizations) / len(utilizations) if utilizations else None

    active_deployments = (
        db.query(func.count(Deployment.id)).filter(Deployment.status == DeploymentStatus.HEALTHY).scalar() or 0
    )

    stats = OverviewStats(
        models_total=models_total,
        production_models=production_models_count,
        active_training_jobs=active_jobs,
        training_jobs_last_30_days=jobs_30d,
        datasets_total=datasets_total,
        training_samples_total=training_samples_total,
        gpu_workers_online=gpu_workers_online,
        gpu_workers_total=len(workers),
        avg_gpu_utilization_pct=avg_util,
        active_deployments=active_deployments,
    )

    recent_jobs = db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).limit(5).all()
    production_models = (
        db.query(ModelVersion).filter(ModelVersion.status == ModelVersionStatus.PRODUCTION).limit(10).all()
    )

    return OverviewResponse(stats=stats, recent_training_runs=recent_jobs, production_models=production_models)
