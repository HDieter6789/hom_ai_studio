import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import (
    audit,
    auth,
    datasets,
    deployments,
    evaluations,
    internal,
    models,
    overview,
    registry,
    training,
    workers,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hom.api")

settings = get_settings()

app = FastAPI(
    title="H.O.M AI Studio API",
    description="Backend API for configuring, training, evaluating and deploying CRM-specialized LLMs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.exception("Unhandled error while processing %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}


for router in (
    auth.router,
    overview.router,
    datasets.router,
    models.router,
    training.router,
    evaluations.router,
    registry.router,
    deployments.router,
    workers.router,
    audit.router,
    internal.router,
):
    app.include_router(router)
