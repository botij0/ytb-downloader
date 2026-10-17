import yt_dlp
from pydantic import BaseModel

from .urls import normalize_youtube_url


class VideoMetadata(BaseModel):
    title: str
    duration_secs: int
    thumbnail_url: str
    uploader: str


class MetadataUnavailable(Exception):
    pass


def fetch_metadata(url: str) -> VideoMetadata:
    canonical = normalize_youtube_url(url)
    opts = {
        "quiet": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(canonical, download=False)
    except MetadataUnavailable:
        raise
    except Exception as exc:
        raise MetadataUnavailable(f"video unavailable: {exc}") from exc
    if not info:
        raise MetadataUnavailable("video unavailable: no metadata returned")
    title = info.get("title")
    if not title:
        raise MetadataUnavailable("video unavailable: missing title")
    duration = info.get("duration") or 0
    return VideoMetadata(
        title=str(title),
        duration_secs=int(duration),
        thumbnail_url=str(info.get("thumbnail") or ""),
        uploader=str(info.get("uploader") or info.get("channel") or ""),
    )
