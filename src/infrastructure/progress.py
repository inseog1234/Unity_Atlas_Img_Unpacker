from __future__ import annotations

from queue import Queue

from src.domain.events import ProgressEvent


class QueueProgressObserver:
    def __init__(self) -> None:
        self.queue: Queue[ProgressEvent] = Queue()

    def publish(self, event: ProgressEvent) -> None:
        self.queue.put(event)
