from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation
from app.services.registry_service import get_version
from hom_core.schemas.evaluation import EvaluationMetrics


def create_evaluation(
    db: Session, *, model_version_id: str, dataset_id: str | None, metrics: EvaluationMetrics, sample_count: int, notes: str | None, actor: str
) -> Evaluation:
    version = get_version(db, model_version_id)  # 404s if missing
    evaluation = Evaluation(
        model_version_id=model_version_id,
        dataset_id=dataset_id,
        metrics=metrics.model_dump(),
        sample_count=sample_count,
        notes=notes,
        created_by=actor,
    )
    db.add(evaluation)

    version.evaluation_metrics = metrics.model_dump()
    db.add(version)

    db.commit()
    db.refresh(evaluation)
    return evaluation


def list_evaluations(db: Session, model_version_id: str | None = None) -> list[Evaluation]:
    query = db.query(Evaluation)
    if model_version_id:
        query = query.filter(Evaluation.model_version_id == model_version_id)
    return query.order_by(Evaluation.created_at.desc()).all()


def compare(db: Session, version_id_a: str, version_id_b: str) -> dict:
    a = get_version(db, version_id_a)
    b = get_version(db, version_id_b)
    metrics_a = a.evaluation_metrics or {}
    metrics_b = b.evaluation_metrics or {}
    keys = sorted(set(metrics_a) | set(metrics_b))
    diff = {}
    for key in keys:
        va, vb = metrics_a.get(key), metrics_b.get(key)
        delta = (vb - va) if isinstance(va, (int, float)) and isinstance(vb, (int, float)) else None
        diff[key] = {"a": va, "b": vb, "delta": delta}
    return {
        "a": {"id": a.id, "display_name": a.display_name},
        "b": {"id": b.id, "display_name": b.display_name},
        "metrics": diff,
    }
