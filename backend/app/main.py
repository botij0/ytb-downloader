from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .jobs import DownloadCreate, DownloadJob, create_job, get_job, run_job


class HealthResponse(BaseModel):
    status: Literal["ok"]


app = FastAPI()

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
    job = create_job(payload)
    background_tasks.add_task(run_job, job.id)
    return job


@app.get("/api/downloads/{job_id}")
def get_download(job_id: str) -> DownloadJob:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job
