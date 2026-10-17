import sys
from pathlib import Path
from typing import Self

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yt_dlp

from app.metadata import MetadataUnavailable, fetch_metadata

VIDEO_ID = "dQw4w9WgXcQ"
CANONICAL = f"https://www.youtube.com/watch?v={VIDEO_ID}"

CANNED_INFO = {
    "title": "Never Gonna Give You Up",
    "duration": 212,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    "uploader": "Rick Astley",
}


class CannedYDL:
    captured: dict | None = None

    def __init__(self, opts: dict) -> None:
        self.opts = opts

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def extract_info(self, url: str, download: bool) -> dict:
        CannedYDL.captured = {"url": url, "download": download}
        assert download is False
        return dict(CANNED_INFO)


class UnavailableYDL(CannedYDL):
    def extract_info(self, url: str, download: bool) -> dict:
        CannedYDL.captured = {"url": url, "download": download}
        raise yt_dlp.utils.DownloadError("ERROR: Video unavailable")


def test_maps_info_to_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yt_dlp, "YoutubeDL", CannedYDL)
    CannedYDL.captured = None

    result = fetch_metadata(CANONICAL)

    assert result.title == "Never Gonna Give You Up"
    assert result.duration_secs == 212
    assert result.thumbnail_url == "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
    assert result.uploader == "Rick Astley"
    assert CannedYDL.captured == {"url": CANONICAL, "download": False}


def test_invalid_url_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yt_dlp, "YoutubeDL", CannedYDL)
    CannedYDL.captured = None

    with pytest.raises(ValueError):
        fetch_metadata("https://example.com/x")

    assert CannedYDL.captured is None


def test_unavailable_raises_metadata_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(yt_dlp, "YoutubeDL", UnavailableYDL)
    CannedYDL.captured = None

    with pytest.raises(MetadataUnavailable, match="(?i)unavailable"):
        fetch_metadata(CANONICAL)
