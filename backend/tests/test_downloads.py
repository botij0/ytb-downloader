from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.jobs import DownloadCreate, create_job, get_job, run_job


def test_create_video_job(client: TestClient) -> None:
    response = client.post(
        "/api/downloads",
        json={"url": "https://example.com/video", "kind": "video"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://example.com/video"
    assert body["kind"] == "video"
    assert body["status"] == "queued"
    assert body["id"]


def test_create_audio_job(client: TestClient) -> None:
    response = client.post(
        "/api/downloads",
        json={"url": "https://example.com/audio", "kind": "audio"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://example.com/audio"
    assert body["kind"] == "audio"
    assert body["status"] == "queued"
    assert body["id"]


def test_job_transitions_to_done(client: TestClient) -> None:
    created = client.post(
        "/api/downloads",
        json={"url": "https://example.com/video", "kind": "video"},
    ).json()

    response = client.get(f"/api/downloads/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["status"] == "done"
    assert body["error"] is None
    assert body["file_path"] is not None
    assert Path(body["file_path"]).is_file()


def test_done_job_serves_file(client: TestClient) -> None:
    created = client.post(
        "/api/downloads",
        json={"url": "https://example.com/video", "kind": "video"},
    ).json()

    response = client.get(f"/api/downloads/{created['id']}/file")

    assert response.status_code == 200
    assert response.content == b"fake-download"


def test_queued_job_file_conflicts(client: TestClient) -> None:
    job = create_job(DownloadCreate(url="https://example.com/pending", kind="video"))

    status_response = client.get(f"/api/downloads/{job.id}")
    file_response = client.get(f"/api/downloads/{job.id}/file")

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"
    assert file_response.status_code == 409


def test_get_unknown_job_returns_404(client: TestClient) -> None:
    response = client.get("/api/downloads/does-not-exist")

    assert response.status_code == 404


def test_get_unknown_job_file_returns_404(client: TestClient) -> None:
    response = client.get("/api/downloads/does-not-exist/file")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"kind": "video"},
        {"url": "https://example.com/video"},
        {"url": "https://example.com/video", "kind": "clip"},
        {"url": 123, "kind": "video"},
    ],
)
def test_malformed_body_returns_422(client: TestClient, payload: dict) -> None:
    response = client.post("/api/downloads", json=payload)

    assert response.status_code == 422


def test_run_job_failed_path(client: TestClient) -> None:
    job = create_job(DownloadCreate(url="https://example.com/broken", kind="video"))

    class RaisingEngine:
        def download(self, url: str, kind: str) -> Path:
            raise RuntimeError("boom")

    result = run_job(job.id, engine=RaisingEngine())

    assert result.status == "failed"
    assert result.error == "boom"

    stored = get_job(job.id)
    assert stored is not None
    assert stored.status == "failed"

    status_response = client.get(f"/api/downloads/{job.id}")
    file_response = client.get(f"/api/downloads/{job.id}/file")

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "failed"
    assert file_response.status_code == 409


def test_run_job_done_path(tmp_path: Path) -> None:
    target = tmp_path / "out.bin"

    class WritingEngine:
        def download(self, url: str, kind: str) -> Path:
            target.write_bytes(b"local-bytes")
            return target

    job = create_job(DownloadCreate(url="https://example.com/local", kind="audio"))
    result = run_job(job.id, engine=WritingEngine())

    assert result.status == "done"
    assert result.error is None
    assert result.file_path == str(target)
    assert target.read_bytes() == b"local-bytes"
