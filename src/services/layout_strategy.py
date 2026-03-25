from __future__ import annotations

from collections import defaultdict
import os
from typing import Callable

from PIL import Image
from PIL.Image import Image as PILImage

from src.domain.entities import SpriteRecord
from src.domain.interfaces import LayoutStrategy, SpriteExtractor


class StableCanvasLayoutStrategy(LayoutStrategy):
    def build_group_sizes(
        self,
        records: list[SpriteRecord],
        atlas_lookup: Callable[[str], PILImage],
        extractor: SpriteExtractor,
    ) -> dict[str, tuple[int, int]]:
        groups: dict[str, list[SpriteRecord]] = defaultdict(list)
        for record in records:
            groups[self._group_key(record)].append(record)

        result: dict[str, tuple[int, int]] = {}
        for group_key, group_records in groups.items():
            max_width = 0
            max_height = 0
            for record in group_records:
                sprite = extractor.extract(record, atlas_lookup(record.scollectionname))
                frame_width = record.sxr + sprite.width
                frame_height = record.syr + sprite.height
                max_width = max(max_width, frame_width)
                max_height = max(max_height, frame_height)
            result[group_key] = (max_width, max_height)

        return result

    def compose_frame(
        self,
        record: SpriteRecord,
        sprite: PILImage,
        group_sizes: dict[str, tuple[int, int]],
    ) -> PILImage:
        group_key = self._group_key(record)
        canvas_width, canvas_height = group_sizes[group_key]
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        canvas.alpha_composite(sprite, (record.sxr, record.syr))
        return canvas

    @staticmethod
    def _group_key(record: SpriteRecord) -> str:
        return os.path.dirname(record.spath)
