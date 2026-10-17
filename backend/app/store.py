from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .jobs import DownloadJob

DB_FILENAME = "jobs.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    kind TEXT NOT NULL,
    quality TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    file_path TEXT,
    progress_percent REAL,
    speed_bps REAL,
    eta_secs REAL
)
"""


def db_path() -> Path:
    from .engine import DOWNLOAD_DIR

    return DOWNLOAD_DIR / DB_FILENAME


def _connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _row_to_job(row: sqlite3.Row) -> DownloadJob:
    from .jobs import DownloadJob

    return DownloadJob(
        id=row["id"],
        url=row["url"],
        kind=row["kind"],
        quality=row["quality"],
        status=row["status"],
        error=row["error"],
        file_path=row["file_path"],
        progress_percent=row["progress_percent"],
        speed_bps=row["speed_bps"],
        eta_secs=row["eta_secs"],
    )


def insert_job(job: DownloadJob) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO jobs"
            " (id, url, kind, quality, status, error, file_path,"
            " progress_percent, speed_bps, eta_secs)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job.id,
                job.url,
                job.kind,
                job.quality,
                job.status,
                job.error,
                job.file_path,
                job.progress_percent,
                job.speed_bps,
                job.eta_secs,
            ),
        )
        conn.commit()


def get_job(job_id: str) -> DownloadJob | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, url, kind, quality, status, error, file_path,"
            " progress_percent, speed_bps, eta_secs FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_job(row)


def list_jobs() -> list[DownloadJob]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, url, kind, quality, status, error, file_path,"
            " progress_percent, speed_bps, eta_secs FROM jobs"
            " ORDER BY rowid DESC"
        ).fetchall()
    return [_row_to_job(row) for row in rows]


def save_job(job: DownloadJob) -> None:
    insert_job(job)


def mark_downloading_failed(message: str) -> list[DownloadJob]:
    with _connect() as conn:
        ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM jobs WHERE status = 'downloading'"
            ).fetchall()
        ]
        if ids:
            conn.execute(
                "UPDATE jobs SET status = 'failed', error = ?"
                " WHERE status = 'downloading'",
                (message,),
            )
            conn.commit()
        rows = []
        for job_id in ids:
            row = conn.execute(
                "SELECT id, url, kind, quality, status, error, file_path,"
                " progress_percent, speed_bps, eta_secs FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if row is not None:
                rows.append(row)
    return [_row_to_job(row) for row in rows]


def clear_all() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM jobs")
        conn.commit()
