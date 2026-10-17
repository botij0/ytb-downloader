from pathlib import Path

import pytest

from app import engine as engine_module
from app import store
from app.jobs import (
    DownloadCreate,
    create_job,
    get_job,
    list_jobs,
    recover_incomplete,
    run_job,
)


@pytest.fixture()
def isolated_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(engine_module, "DOWNLOAD_DIR", tmp_path)
    return tmp_path


def test_create_get_roundtrip(isolated_store: Path) -> None:
    job = create_job(
        DownloadCreate(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", kind="video")
    )

    stored = get_job(job.id)

    assert stored is not None
    assert stored.id == job.id
    assert stored.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert stored.kind == "video"
    assert stored.status == "queued"
    assert (isolated_store / "jobs.db").is_file()


def test_list_ordering_newest_first(isolated_store: Path) -> None:
    first = create_job(DownloadCreate(url="https://example.com/1", kind="video"))
    second = create_job(DownloadCreate(url="https://example.com/2", kind="audio"))
    third = create_job(DownloadCreate(url="https://example.com/3", kind="video"))

    jobs = list_jobs()

    assert [j.id for j in jobs] == [third.id, second.id, first.id]


def test_recover_incomplete_flips_downloading(isolated_store: Path) -> None:
    job = create_job(DownloadCreate(url="https://example.com/hung", kind="video"))
    stored = get_job(job.id)
    assert stored is not None
    stored.status = "downloading"
    store.save_job(stored)

    recovered = recover_incomplete()

    assert len(recovered) == 1
    assert recovered[0].id == job.id
    flipped = get_job(job.id)
    assert flipped is not None
    assert flipped.status == "failed"
    assert flipped.error == "server restarted while downloading"


def test_done_jobs_survive_recover(isolated_store: Path, tmp_path: Path) -> None:
    target = tmp_path / "out.bin"

    class WritingEngine:
        def download(
            self, url: str, kind: str, quality: str = "best", on_progress=None
        ) -> Path:
            target.write_bytes(b"keep-me")
            return target

    done_job = create_job(DownloadCreate(url="https://example.com/done", kind="audio"))
    run_job(done_job.id, engine=WritingEngine())

    hanging = create_job(DownloadCreate(url="https://example.com/hung", kind="video"))
    hanging_row = get_job(hanging.id)
    assert hanging_row is not None
    hanging_row.status = "downloading"
    store.save_job(hanging_row)

    recover_incomplete()

    done_stored = get_job(done_job.id)
    assert done_stored is not None
    assert done_stored.status == "done"
    assert done_stored.file_path == str(target)

    hung_stored = get_job(hanging.id)
    assert hung_stored is not None
    assert hung_stored.status == "failed"
    assert hung_stored.error == "server restarted while downloading"
