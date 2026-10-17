from fastapi.testclient import TestClient

from app.engine import format_for

VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_format_best_video() -> None:
    assert format_for("video", "best") == "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"


def test_format_1080p_video() -> None:
    result = format_for("video", "1080p")
    assert "height<=1080" in result
    assert "mp4" in result


def test_format_720p_video() -> None:
    result = format_for("video", "720p")
    assert "height<=720" in result
    assert "mp4" in result


def test_format_480p_video() -> None:
    result = format_for("video", "480p")
    assert "height<=480" in result
    assert "mp4" in result


def test_format_audio_ignores_quality() -> None:
    expected = "ba[ext=m4a]/ba"
    assert format_for("audio", "best") == expected
    assert format_for("audio", "1080p") == expected
    assert format_for("audio", "720p") == expected
    assert format_for("audio", "480p") == expected


def test_post_accepts_each_quality(client: TestClient) -> None:
    for quality in ["best", "1080p", "720p", "480p"]:
        response = client.post(
            "/api/downloads",
            json={"url": VIDEO_URL, "kind": "video", "quality": quality},
        )
        assert response.status_code == 200


def test_post_rejects_invalid_quality(client: TestClient) -> None:
    response = client.post(
        "/api/downloads",
        json={"url": VIDEO_URL, "kind": "video", "quality": "8k"},
    )
    assert response.status_code == 422
