from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

JobStatus = Literal["queued", "downloading", "done", "failed"]
DownloadKind = Literal["video", "audio"]


class DownloadCreate(BaseModel):
    url: str
    kind: DownloadKind


class DownloadJob(BaseModel):
    id: str
    url: str
    kind: DownloadKind
    status: JobStatus
    error: str | None = None


_jobs: dict[str, DownloadJob] = {}


def create_job(data: DownloadCreate) -> DownloadJob:
    job = DownloadJob(
        id=uuid4().hex, url=data.url, kind=data.kind, status="queued", error=None
    )
    _jobs[job.id] = job
    return job


def get_job(job_id: str) -> DownloadJob | None:
    return _jobs.get(job_id)
