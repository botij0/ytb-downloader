import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.urls import normalize_youtube_url

VIDEO_ID = "dQw4w9WgXcQ"
CANONICAL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def test_short_link():
    assert normalize_youtube_url(f"https://youtu.be/{VIDEO_ID}") == CANONICAL


def test_watch_link_ignores_extra_params():
    url = f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PL123&t=42s"
    assert normalize_youtube_url(url) == CANONICAL


def test_shorts_link():
    assert (
        normalize_youtube_url(f"https://www.youtube.com/shorts/{VIDEO_ID}") == CANONICAL
    )


def test_music_link():
    url = f"https://music.youtube.com/watch?v={VIDEO_ID}&list=OLAK5uy_test"
    assert normalize_youtube_url(url) == CANONICAL


def test_rejects_non_youtube_host():
    with pytest.raises(ValueError, match="(?i)youtube"):
        normalize_youtube_url("https://example.com/x")


def test_rejects_malformed_string():
    with pytest.raises(ValueError, match="(?i)malformed|valid"):
        normalize_youtube_url("not a url")


def test_rejects_empty_string():
    with pytest.raises(ValueError, match="(?i)empty"):
        normalize_youtube_url("   ")
