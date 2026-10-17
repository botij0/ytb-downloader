from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import yt_dlp

if TYPE_CHECKING:
    from .jobs import DownloadKind, VideoQuality

DOWNLOAD_DIR = Path(os.environ.get("YTB_DOWNLOAD_DIR", "./downloads"))

_OPTIONS_BY_KIND = {
    "video": {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
    },
    "audio": {
        "format": "ba[ext=m4a]/ba",
    },
}


def format_for(kind: DownloadKind, quality: VideoQuality) -> str:
    if kind == "audio":
        return "ba[ext=m4a]/ba"
    if quality == "1080p":
        return "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4][height<=1080]/b[height<=1080]/b"
    if quality == "720p":
        return "bv*[ext=mp4][height<=720]+ba[ext=m4a]/b[ext=mp4][height<=720]/b[height<=720]/b"
    if quality == "480p":
        return "bv*[ext=mp4][height<=480]+ba[ext=m4a]/b[ext=mp4][height<=480]/b[height<=480]/b"
    return "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"


class Downloader(Protocol):
    def download(
        self, url: str, kind: DownloadKind, quality: VideoQuality = "best"
    ) -> Path: ...


class YtDlpEngine:
    def download(
        self, url: str, kind: DownloadKind, quality: VideoQuality = "best"
    ) -> Path:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        opts = {
            "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
            "noplaylist": True,
            "format": format_for(kind, quality),
        }
        if kind == "video":
            opts["merge_output_format"] = "mp4"
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
            if path.exists():
                return path
            merged = path.with_suffix(".mp4")
            if merged.exists():
                return merged
            return path
