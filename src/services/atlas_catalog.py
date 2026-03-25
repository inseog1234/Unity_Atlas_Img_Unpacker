from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL.Image import Image as PILImage

from src.domain.entities import AtlasSet
from src.domain.interfaces import AtlasCatalog, AtlasCatalogFactoryInterface, AtlasLoader


def normalize_collection_name(name: str) -> str:
    return Path(name).stem.strip().lower()


@dataclass(frozen=True)
class InMemoryAtlasCatalog(AtlasCatalog):
    images_by_key: dict[str, PILImage]
    source_paths_by_key: dict[str, Path]

    def get(self, collection_name: str) -> PILImage:
        key = normalize_collection_name(collection_name)
        if key not in self.images_by_key:
            known = ", ".join(sorted(self.source_paths_by_key.keys()))
            raise KeyError(f"아틀라스 '{collection_name}' 을(를) 찾지 못했습니다. 사용 가능 키: {known}")
        return self.images_by_key[key]

    def get_source_path(self, collection_name: str) -> Path:
        key = normalize_collection_name(collection_name)
        if key not in self.source_paths_by_key:
            known = ", ".join(sorted(self.source_paths_by_key.keys()))
            raise KeyError(f"아틀라스 '{collection_name}' 을(를) 찾지 못했습니다. 사용 가능 키: {known}")
        return self.source_paths_by_key[key]

    def contains(self, collection_name: str) -> bool:
        return normalize_collection_name(collection_name) in self.images_by_key


class AtlasCatalogFactory(AtlasCatalogFactoryInterface):
    def create(self, atlas_set: AtlasSet, atlas_loader: AtlasLoader) -> AtlasCatalog:
        images_by_key: dict[str, PILImage] = {}
        source_paths_by_key: dict[str, Path] = {}

        for atlas_path in atlas_set.atlas_paths:
            key = normalize_collection_name(atlas_path.name)
            if key in images_by_key:
                raise ValueError(f"중복 아틀라스 이름이 있습니다: {atlas_path.name}")
            images_by_key[key] = atlas_loader.load(atlas_path)
            source_paths_by_key[key] = atlas_path

        return InMemoryAtlasCatalog(
            images_by_key=images_by_key,
            source_paths_by_key=source_paths_by_key,
        )
