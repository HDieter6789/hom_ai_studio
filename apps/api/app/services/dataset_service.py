import io

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.dataset import Dataset
from app.services import audit_service
from app.services.dataset_validation import validate_dataset
from app.services.storage import get_storage
from hom_core.enums import AuditAction, DatasetFormat, DatasetStatus, DatasetType

ALLOWED_EXTENSIONS = {"json", "jsonl", "csv"}


def _extension(filename: str) -> str:
    if "." not in filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must have an extension (.json/.jsonl/.csv)")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported file type '.{ext}'")
    return ext


async def upload_dataset(
    db: Session,
    *,
    name: str,
    description: str | None,
    dataset_type: DatasetType,
    file: UploadFile,
    actor: str,
) -> Dataset:
    settings = get_settings()
    ext = _extension(file.filename or "")

    raw = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(raw) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds the {settings.max_upload_size_mb}MB upload limit",
        )
    if len(raw) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")

    dataset = Dataset(
        name=name,
        description=description,
        type=dataset_type,
        format=DatasetFormat(ext),
        status=DatasetStatus.VALIDATING,
        storage_key="",
        file_size_bytes=len(raw),
        created_by=actor,
    )
    db.add(dataset)
    db.flush()  # obtain dataset.id before building the storage key

    storage = get_storage()
    key = f"datasets/{dataset.id}/source.{ext}"
    storage.save(key, io.BytesIO(raw))
    dataset.storage_key = key

    result = validate_dataset(raw, ext)
    dataset.status = DatasetStatus.READY if result.is_valid else DatasetStatus.INVALID
    dataset.sample_count = result.stats.sample_count
    dataset.schema_info = result.schema_info.model_dump()
    dataset.stats = result.stats.model_dump()
    dataset.validation_errors = result.errors

    db.commit()
    db.refresh(dataset)

    audit_service.log(
        db,
        action=AuditAction.DATASET_UPLOADED,
        actor=actor,
        target_type="dataset",
        target_id=dataset.id,
        metadata={"name": name, "sample_count": dataset.sample_count},
    )
    return dataset


def list_datasets(db: Session) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


def get_dataset(db: Session, dataset_id: str) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found")
    return dataset


def preview_samples(db: Session, dataset_id: str, limit: int = 20) -> list[dict]:
    dataset = get_dataset(db, dataset_id)
    storage = get_storage()
    from app.services.dataset_validation import parse_samples

    raw = storage.open(dataset.storage_key).read()
    samples = parse_samples(raw, dataset.format.value)
    return [s for s in samples[:limit] if isinstance(s, dict)]


def delete_dataset(db: Session, dataset_id: str, actor: str) -> None:
    dataset = get_dataset(db, dataset_id)
    storage = get_storage()
    if storage.exists(dataset.storage_key):
        storage.delete(dataset.storage_key)
    db.delete(dataset)
    db.commit()
    audit_service.log(
        db,
        action=AuditAction.DATASET_DELETED,
        actor=actor,
        target_type="dataset",
        target_id=dataset_id,
        metadata={"name": dataset.name},
    )
