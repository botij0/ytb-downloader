from pathlib import Path

from app.jobs import DownloadCreate, create_job, get_job, run_job


def test_run_job_reports_progress(tmp_path: Path) -> None:
    target = tmp_path / "out.bin"
    observed: list[tuple[str, float | None, float | None, float | None]] = []

    class HookEngine:
        def download(
            self, url: str, kind: str, quality: str = "best", on_progress=None
        ) -> Path:
            assert on_progress is not None
            on_progress(10.0, 1000.0, 9.0)
            observed.append(
                (job.status, job.progress_percent, job.speed_bps, job.eta_secs)
            )
            on_progress(55.0, 2000.0, 4.0)
            observed.append(
                (job.status, job.progress_percent, job.speed_bps, job.eta_secs)
            )
            target.write_bytes(b"progress-bytes")
            return target

    job = create_job(DownloadCreate(url="https://example.com/progress", kind="audio"))
    assert job.progress_percent is None
    assert job.speed_bps is None
    assert job.eta_secs is None

    result = run_job(job.id, engine=HookEngine())

    assert observed == [
        ("downloading", 10.0, 1000.0, 9.0),
        ("downloading", 55.0, 2000.0, 4.0),
    ]
    assert observed[1][1] is not None and observed[0][1] is not None
    assert observed[1][1] > observed[0][1]
    assert result.status == "done"
    assert result.progress_percent == 100.0
    stored = get_job(job.id)
    assert stored is not None
    assert stored.progress_percent == 100.0
