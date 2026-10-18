from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import engine as engine_module
from app import jobs, main


class FakeEngine:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def download(
        self, url: str, kind: str, quality: str = "best", on_progress=None
    ) -> Path:
        self.file_path.write_bytes(b"fake-download")
        return self.file_path


@pytest.fixture(scope="session", autouse=True)
def temp_download_dir(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    directory = tmp_path_factory.mktemp("downloads")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(engine_module, "DOWNLOAD_DIR", directory)
        patch.setattr(main, "DOWNLOAD_DIR", directory)
        yield


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
    with TestClient(main.app) as test_client:
        yield test_client
