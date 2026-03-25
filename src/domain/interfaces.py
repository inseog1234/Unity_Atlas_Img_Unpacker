from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from threading import Event
from typing import Callable, Protocol

from PIL.Image import Image

from src.domain.entities import AtlasSet, ParseRequest, ParseSummary, SpriteRecord
from src.domain.events import ProgressEvent


class MetadataLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> dict:
        raise NotImplementedError


class AtlasLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> Image:
        raise NotImplementedError


class SpriteExtractor(ABC):
    @abstractmethod
    def extract(self, record: SpriteRecord, atlas_image: Image) -> Image:
        raise NotImplementedError


class LayoutStrategy(ABC):
    @abstractmethod
    def build_group_sizes(
        self,
        records: list[SpriteRecord],
        atlas_lookup: Callable[[str], Image],
        extractor: SpriteExtractor,
    ) -> dict[str, tuple[int, int]]:
        raise NotImplementedError

    @abstractmethod
    def compose_frame(
        self,
        record: SpriteRecord,
        sprite: Image,
        group_sizes: dict[str, tuple[int, int]],
    ) -> Image:
        raise NotImplementedError


class AtlasCatalog(ABC):
    @abstractmethod
    def get(self, collection_name: str) -> Image:
        raise NotImplementedError

    @abstractmethod
    def get_source_path(self, collection_name: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    def contains(self, collection_name: str) -> bool:
        raise NotImplementedError


class AtlasCatalogFactoryInterface(ABC):
    @abstractmethod
    def create(self, atlas_set: AtlasSet, atlas_loader: AtlasLoader) -> AtlasCatalog:
        raise NotImplementedError


class ProgressObserver(Protocol):
    def publish(self, event: ProgressEvent) -> None:
        ...


class ParserService(ABC):
    @abstractmethod
    def parse(
        self,
        request: ParseRequest,
        cancel_event: Event,
        observer: ProgressObserver,
    ) -> ParseSummary:
        raise NotImplementedError
