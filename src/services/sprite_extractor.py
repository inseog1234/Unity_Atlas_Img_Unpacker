from __future__ import annotations

from PIL import Image, ImageOps
from PIL.Image import Image as PILImage

from src.domain.entities import SpriteRecord
from src.domain.interfaces import SpriteExtractor


class HollowKnightSpriteExtractor(SpriteExtractor):
    def extract(self, record: SpriteRecord, atlas_image: PILImage) -> PILImage:
        _, atlas_height = atlas_image.size

        crop_width = record.sheight if record.sfilpped else record.swidth
        crop_height = record.swidth if record.sfilpped else record.sheight

        left = record.sx
        top = atlas_height - record.sy - crop_height
        right = left + crop_width
        bottom = atlas_height - record.sy

        sprite = atlas_image.crop((left, top, right, bottom))

        if record.sfilpped:
            sprite = sprite.transpose(Image.Transpose.ROTATE_90)

        return sprite