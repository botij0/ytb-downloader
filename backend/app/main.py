import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .engine import DOWNLOAD_DIR
from .jobs import (
    DownloadCreate,
    DownloadJob,
    create_job,
    get_job,
    list_jobs,
    recover_incomplete,
)
from .metadata import MetadataUnavailable, VideoMetadata, fetch_metadata
from .urls import normalize_youtube_url
from .worker import enqueue, start_worker, stop_worker


class HealthResponse(BaseModel):
    status: Literal["ok"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    recover_incomplete()
    start_worker()
    try:
        yield
    finally:
        stop_worker()


app = FastAPI(lifespan=lifespan)


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS")
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def get_health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/downloads")
def post_download(payload: DownloadCreate) -> DownloadJob:
    try:
        canonical = normalize_youtube_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = create_job(
        DownloadCreate(url=canonical, kind=payload.kind, quality=payload.quality)
    )
    enqueue(job.id)
    return job.model_copy()


@app.get("/api/downloads")
def list_downloads() -> list[DownloadJob]:
    return list_jobs()


@app.get("/api/downloads/{job_id}")
def get_download(job_id: str) -> DownloadJob:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/downloads/{job_id}/file")
def get_download_file(job_id: str) -> FileResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status != "done" or job.file_path is None:
        raise HTTPException(status_code=409, detail="download is not ready")
    path = Path(job.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path, filename=path.name)


@app.get("/api/metadata")
def get_metadata(url: str) -> VideoMetadata:
    try:
        return fetch_metadata(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MetadataUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
