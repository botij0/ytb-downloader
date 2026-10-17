import threading
import time
from pathlib import Path

import pytest

from app import worker
from app.jobs import DownloadCreate, create_job, get_job


def _wait_until(predicate, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    return bool(predicate())


def test_serial_worker_runs_one_at_a_time(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    entered = threading.Event()
    release = threading.Event()
    calls: list[str] = []
    lock = threading.Lock()

    class BlockingEngine:
        def download(
            self, url: str, kind: str, quality: str = "best", on_progress=None
        ) -> Path:
            with lock:
                calls.append(url)
                first = len(calls) == 1
            if first:
                entered.set()
                assert release.wait(timeout=10.0)
            target = tmp_path / f"out-{len(calls)}.bin"
            target.write_bytes(b"serial-bytes")
            return target

    monkeypatch.setattr("app.engine.YtDlpEngine", lambda: BlockingEngine())

    worker.start_worker()
    try:
        first = create_job(
            DownloadCreate(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", kind="audio"
            )
        )
        second = create_job(
            DownloadCreate(
                url="https://www.youtube.com/watch?v=aqz-KE-bpKQ", kind="audio"
            )
        )
        worker.enqueue(first.id)
        worker.enqueue(second.id)

        assert entered.wait(timeout=10.0)
        assert _wait_until(lambda: (get_job(first.id) or first).status == "downloading")
        time.sleep(0.3)
        first_stored = get_job(first.id)
        second_stored = get_job(second.id)
        assert first_stored is not None
        assert second_stored is not None
        assert first_stored.status == "downloading"
        assert second_stored.status == "queued"

        release.set()
        time.sleep(0.5)
        assert _wait_until(
            lambda: (
                (get_job(first.id) or first).status == "done"
                and (get_job(second.id) or second).status == "done"
            )
        )
        assert calls == [first.url, second.url]
    finally:
        release.set()
        worker.stop_worker()
