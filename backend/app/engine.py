from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import yt_dlp

if TYPE_CHECKING:
    from .jobs import DownloadKind

DOWNLOAD_DIR = Path(__file__).resolve().parent / "downloads"


class Downloader(Protocol):
    def download(self, url: str, kind: DownloadKind) -> Path: ...


class YtDlpEngine:
    def download(self, url: str, kind: DownloadKind) -> Path:
        if kind == "audio":
            raise NotImplementedError("audio downloads arrive in issue #5")
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        opts = {
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
            "merge_output_format": "mp4",
            "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
            "noplaylist": True,
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
