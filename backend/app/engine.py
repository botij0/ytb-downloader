from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import yt_dlp

if TYPE_CHECKING:
    from .jobs import DownloadKind, VideoQuality

DOWNLOAD_DIR = Path(os.environ.get("YTB_DOWNLOAD_DIR", "./downloads"))


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


ProgressHook = Callable[[float | None, float | None, float | None], None]


class Downloader(Protocol):
    def download(
        self,
        url: str,
        kind: DownloadKind,
        quality: VideoQuality = "best",
        on_progress: ProgressHook | None = None,
    ) -> Path: ...


class YtDlpEngine:
    def download(
        self,
        url: str,
        kind: DownloadKind,
        quality: VideoQuality = "best",
        on_progress: ProgressHook | None = None,
    ) -> Path:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

        def _progress_hook(status: dict) -> None:
            if on_progress is None:
                return
            state = status.get("status")
            speed = status.get("speed")
            eta = status.get("eta")
            speed_value = float(speed) if speed is not None else None
            eta_value = float(eta) if eta is not None else None
            if state == "finished":
                on_progress(100.0, speed_value, eta_value)
                return
            if state != "downloading":
                return
            downloaded = status.get("downloaded_bytes", status.get("downloaded"))
            total = status.get("total_bytes", status.get("total_bytes_estimate"))
            percent: float | None = None
            if (
                isinstance(downloaded, (int, float))
                and isinstance(total, (int, float))
                and total > 0
            ):
                percent = min(100.0, max(0.0, float(downloaded) / float(total) * 100.0))
            on_progress(percent, speed_value, eta_value)

        opts = {
            "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
            "noplaylist": True,
            "format": format_for(kind, quality),
            "progress_hooks": [_progress_hook],
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
