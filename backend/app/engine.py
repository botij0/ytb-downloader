from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import yt_dlp

if TYPE_CHECKING:
    from .jobs import DownloadKind

DOWNLOAD_DIR = Path(__file__).resolve().parent / "downloads"

_OPTIONS_BY_KIND = {
    "video": {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
    },
    "audio": {
        "format": "ba[ext=m4a]/ba",
    },
}


class Downloader(Protocol):
    def download(self, url: str, kind: DownloadKind) -> Path: ...


class YtDlpEngine:
    def download(self, url: str, kind: DownloadKind) -> Path:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        opts = {
            "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
            "noplaylist": True,
            **_OPTIONS_BY_KIND[kind],
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
            if path.exists():
                return path
            merged = path.with_suffix(".mp4")
            if merged.exists():
                return merged
            return path
