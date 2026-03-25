from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from PIL.Image import Image as PILImage

from src.domain.interfaces import AtlasLoader, MetadataLoader


class JsonFileMetadataLoader(MetadataLoader):
    def load(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)


class DiskAtlasLoader(AtlasLoader):
    def load(self, path: Path) -> PILImage:
        return Image.open(path).convert("RGBA")
