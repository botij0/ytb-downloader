from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import BaseModel

from . import store

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


class _JobsCompat(dict[str, DownloadJob]):
    def clear(self) -> None:
        super().clear()
        store.clear_all()


_jobs: _JobsCompat = _JobsCompat()


def _sync_cached(fresh: DownloadJob) -> DownloadJob:
    existing = _jobs.get(fresh.id)
    if existing is None:
        _jobs[fresh.id] = fresh
        return fresh
    for field in type(fresh).model_fields:
        setattr(existing, field, getattr(fresh, field))
    return existing


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
    store.insert_job(job)
    return job


def get_job(job_id: str) -> DownloadJob | None:
    fresh = store.get_job(job_id)
    if fresh is None:
        _jobs.pop(job_id, None)
        return None
    return _sync_cached(fresh)


def list_jobs() -> list[DownloadJob]:
    return [_sync_cached(job) for job in store.list_jobs()]


def recover_incomplete() -> list[DownloadJob]:
    return [
        _sync_cached(job)
        for job in store.mark_downloading_failed("server restarted while downloading")
    ]


def run_job(job_id: str, engine: Downloader | None = None) -> DownloadJob:
    job = get_job(job_id)
    if job is None:
        raise KeyError(job_id)
    if engine is None:
        from .engine import YtDlpEngine

        engine = YtDlpEngine()
    job.status = "downloading"
    store.save_job(job)

    def _on_progress(
        percent: float | None, speed: float | None, eta: float | None
    ) -> None:
        job.progress_percent = percent
        job.speed_bps = speed
        job.eta_secs = eta
        store.save_job(job)

    try:
        path = engine.download(
            job.url, job.kind, quality=job.quality, on_progress=_on_progress
        )
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc) or repr(exc)
        store.save_job(job)
        return job
    job.status = "done"
    job.error = None
    job.file_path = str(path)
    job.progress_percent = 100.0
    store.save_job(job)
    return job
