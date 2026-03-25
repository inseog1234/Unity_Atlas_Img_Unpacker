from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class AtlasSet:
    atlas_paths: tuple[Path, ...]
    info_path: Path
    display_name: str
    source_dir: Path
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class SpriteRecord:
    sid: int
    sx: int
    sy: int
    sxr: int
    syr: int
    swidth: int
    sheight: int
    scollectionname: str
    spath: str
    sfilpped: bool


@dataclass(frozen=True)
class ParseRequest:
    sets: list[AtlasSet]
    output_dir: Path


@dataclass(frozen=True)
class ParseSummary:
    sets_processed: int
    sprites_saved: int
    output_dir: Path
    cancelled: bool = False
    error_message: Optional[str] = None
