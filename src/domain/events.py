from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ProgressEventType(str, Enum):
    STARTED = "started"
    SET_STARTED = "set_started"
    RECORD_SAVED = "record_saved"
    SET_COMPLETED = "set_completed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass(frozen=True)
class ProgressEvent:
    event_type: ProgressEventType
    message: str
    current: int = 0
    total: int = 0
    set_name: str = ""
    current_atlas: str = ""
    current_output: str = ""
    output_dir: Optional[Path] = None
    error_message: str = ""
