from __future__ import annotations

from threading import Event, Lock, Thread
from typing import Callable, Optional

from src.domain.entities import ParseSummary


class BackgroundTaskRunner:
    def __init__(self) -> None:
        self._thread: Optional[Thread] = None
        self._cancel_event = Event()
        self._lock = Lock()

    def run(self, task: Callable[[Event], ParseSummary]) -> None:
        with self._lock:
            if self.is_running:
                raise RuntimeError("이미 작업이 실행 중입니다.")
            self._cancel_event = Event()
            self._thread = Thread(target=task, args=(self._cancel_event,), daemon=True)
            self._thread.start()

    def cancel(self) -> None:
        with self._lock:
            self._cancel_event.set()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
