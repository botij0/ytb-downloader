from __future__ import annotations

import queue
import sqlite3
import threading
from contextlib import suppress

from .jobs import run_job

_work: queue.Queue = queue.Queue()
_thread: threading.Thread | None = None
_sentinel = object()
_lock = threading.Lock()
_ready = threading.Condition(_lock)
_finished: set[str] = set()


def enqueue(job_id: str) -> None:
    _work.put(job_id)


def wait_for(job_id: str) -> None:
    with _ready:
        _ready.wait_for(lambda: job_id in _finished)
        _finished.discard(job_id)


def _loop() -> None:
    while True:
        item = _work.get()
        try:
            if item is _sentinel:
                return
            with suppress(KeyError, sqlite3.OperationalError):
                run_job(item)
            with _ready:
                _finished.add(item)
                _ready.notify_all()
        finally:
            _work.task_done()


def start_worker() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()


def stop_worker() -> None:
    global _thread
    thread = _thread
    if thread is None:
        return
    _work.put(_sentinel)
    thread.join()
    _thread = None
