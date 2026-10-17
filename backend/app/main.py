from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
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
    run_job,
)
from .metadata import MetadataUnavailable, VideoMetadata, fetch_metadata
from .urls import normalize_youtube_url


class HealthResponse(BaseModel):
    status: Literal["ok"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    recover_incomplete()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def get_health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/downloads")
def post_download(
    payload: DownloadCreate, background_tasks: BackgroundTasks
) -> DownloadJob:
    try:
        canonical = normalize_youtube_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = create_job(
        DownloadCreate(url=canonical, kind=payload.kind, quality=payload.quality)
    )
    background_tasks.add_task(run_job, job.id)
    return job


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
    response = FileResponse(path)
    response.headers["content-disposition"] = f'attachment; filename="{path.name}"'
    return response


@app.get("/api/metadata")
def get_metadata(url: str) -> VideoMetadata:
    try:
        return fetch_metadata(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MetadataUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
