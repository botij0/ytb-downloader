from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import jobs
from app.main import app


class FakeEngine:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def download(self, url: str, kind: str) -> Path:
        self.file_path.write_bytes(b"fake-download")
        return self.file_path


@pytest.fixture(autouse=True)
def fake_engine(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[FakeEngine]:
    jobs._jobs.clear()
    fake_file = tmp_path / "fake-download.bin"
    fake_file.write_bytes(b"fake-download")
    engine = FakeEngine(fake_file)
    monkeypatch.setattr("app.engine.YtDlpEngine", lambda: engine)
    monkeypatch.setattr("app.jobs.YtDlpEngine", lambda: engine, raising=False)
    yield engine
    jobs._jobs.clear()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
