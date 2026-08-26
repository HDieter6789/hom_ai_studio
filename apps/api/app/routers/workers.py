from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.models.worker import Worker
from app.schemas.worker import WorkerHeartbeat, WorkerOut
from app.security import verify_internal_token

router = APIRouter(prefix="/api/workers", tags=["workers"])


@router.get("", response_model=list[WorkerOut])
def list_workers(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return db.query(Worker).order_by(Worker.hostname).all()


@router.post("/heartbeat", response_model=WorkerOut, dependencies=[Depends(verify_internal_token)])
def heartbeat(payload: WorkerHeartbeat, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_key == payload.worker_key).first()
    if worker is None:
        worker = Worker(worker_key=payload.worker_key, hostname=payload.hostname)
        db.add(worker)

    worker.hostname = payload.hostname
    worker.status = payload.status
    worker.compute_provider = payload.compute_provider
    worker.gpus = payload.gpus
    worker.running_job_id = payload.running_job_id
    worker.last_heartbeat_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(worker)
    return worker
