from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import BaseModel

if TYPE_CHECKING:
    from .engine import Downloader

JobStatus = Literal["queued", "downloading", "done", "failed"]
DownloadKind = Literal["video", "audio"]
VideoQuality = Literal["best", "1080p", "720p", "480p"]


class DownloadCreate(BaseModel):
    url: str
    kind: DownloadKind
    quality: VideoQuality = "best"


class DownloadJob(BaseModel):
    id: str
    url: str
    kind: DownloadKind
    quality: VideoQuality = "best"
    status: JobStatus
    error: str | None = None
    file_path: str | None = None
    progress_percent: float | None = None
    speed_bps: float | None = None
    eta_secs: float | None = None


_jobs: dict[str, DownloadJob] = {}


def create_job(data: DownloadCreate) -> DownloadJob:
    job = DownloadJob(
        id=uuid4().hex,
        url=data.url,
        kind=data.kind,
        quality=data.quality,
        status="queued",
        error=None,
    )
    _jobs[job.id] = job
    return job


def get_job(job_id: str) -> DownloadJob | None:
    return _jobs.get(job_id)


def run_job(job_id: str, engine: Downloader | None = None) -> DownloadJob:
    job = _jobs[job_id]
    if engine is None:
        from .engine import YtDlpEngine

        engine = YtDlpEngine()
    job.status = "downloading"

    def _on_progress(
        percent: float | None, speed: float | None, eta: float | None
    ) -> None:
        job.progress_percent = percent
        job.speed_bps = speed
        job.eta_secs = eta

    try:
        path = engine.download(
            job.url, job.kind, quality=job.quality, on_progress=_on_progress
        )
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc) or repr(exc)
        return job
    job.status = "done"
    job.error = None
    job.file_path = str(path)
    job.progress_percent = 100.0
    return job
