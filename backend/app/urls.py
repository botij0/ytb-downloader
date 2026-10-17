import re
from urllib.parse import parse_qs, urlparse

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def normalize_youtube_url(raw: str) -> str:
    if not raw or not raw.strip():
        raise ValueError("YouTube URL is empty")
    text = raw.strip()
    parsed = urlparse(text)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"malformed URL: {raw!r} is not a valid URL")
    host = (parsed.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        raise ValueError(
            f"unsupported host: {host or parsed.netloc!r} is not a YouTube URL"
        )
    video_id: str | None = None
    if host in ("youtu.be", "www.youtu.be"):
        segment = parsed.path.strip("/").split("/")[0] if parsed.path.strip("/") else ""
        video_id = segment or None
        if video_id is None:
            raise ValueError("missing video ID in youtu.be URL")
    else:
        path = parsed.path.rstrip("/")
        if path == "/watch":
            values = parse_qs(parsed.query).get("v", [])
            video_id = values[0] if values else None
            if video_id is None:
                raise ValueError("missing video ID in youtube.com watch URL")
        elif path.startswith("/shorts/"):
            parts = path.split("/")
            video_id = parts[2] if len(parts) > 2 and parts[2] else None
            if video_id is None:
                raise ValueError("missing video ID in youtube.com shorts URL")
        else:
            raise ValueError(f"unsupported YouTube URL path: {parsed.path!r}")
    if not _VIDEO_ID_RE.match(video_id):
        raise ValueError(
            f"invalid video ID: {video_id!r} is not a valid YouTube video ID"
        )
    return f"https://www.youtube.com/watch?v={video_id}"
