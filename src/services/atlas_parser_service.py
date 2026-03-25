from __future__ import annotations

from pathlib import Path
from threading import Event

from src.domain.entities import AtlasSet, ParseRequest, ParseSummary
from src.domain.events import ProgressEvent, ProgressEventType
from src.domain.interfaces import (
    AtlasCatalogFactoryInterface,
    AtlasLoader,
    LayoutStrategy,
    MetadataLoader,
    ParserService,
    ProgressObserver,
    SpriteExtractor,
)
from src.services.record_factory import SpriteRecordFactory


class AtlasParserService(ParserService):
    def __init__(
        self,
        metadata_loader: MetadataLoader,
        atlas_loader: AtlasLoader,
        record_factory: SpriteRecordFactory,
        extractor: SpriteExtractor,
        layout_strategy: LayoutStrategy,
        catalog_factory: AtlasCatalogFactoryInterface,
    ) -> None:
        self._metadata_loader = metadata_loader
        self._atlas_loader = atlas_loader
        self._record_factory = record_factory
        self._extractor = extractor
        self._layout_strategy = layout_strategy
        self._catalog_factory = catalog_factory

    def parse(
        self,
        request: ParseRequest,
        cancel_event: Event,
        observer: ProgressObserver,
    ) -> ParseSummary:
        request.output_dir.mkdir(parents=True, exist_ok=True)

        total_sprites = self._count_total_sprites(request.sets)
        saved_count = 0
        processed_sets = 0

        observer.publish(
            ProgressEvent(
                event_type=ProgressEventType.STARTED,
                message="파싱을 시작합니다.",
                current=0,
                total=total_sprites,
                output_dir=request.output_dir,
            )
        )

        for atlas_set in request.sets:
            if cancel_event.is_set():
                return self._cancelled_summary(observer, request.output_dir, processed_sets, saved_count, total_sprites)

            observer.publish(
                ProgressEvent(
                    event_type=ProgressEventType.SET_STARTED,
                    message=f"세트 처리 시작: {atlas_set.display_name}",
                    current=saved_count,
                    total=total_sprites,
                    set_name=atlas_set.display_name,
                )
            )

            raw = self._metadata_loader.load(atlas_set.info_path)
            records = self._record_factory.create_many(raw)
            catalog = self._catalog_factory.create(atlas_set, self._atlas_loader)
            self._validate_required_collections(atlas_set, records, catalog)
            group_sizes = self._layout_strategy.build_group_sizes(records, catalog.get, self._extractor)

            for record in records:
                if cancel_event.is_set():
                    return self._cancelled_summary(observer, request.output_dir, processed_sets, saved_count, total_sprites)

                atlas_image = catalog.get(record.scollectionname)
                atlas_path = catalog.get_source_path(record.scollectionname)
                sprite = self._extractor.extract(record, atlas_image)
                frame = self._layout_strategy.compose_frame(record, sprite, group_sizes)
                output_path = request.output_dir / Path(record.spath)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                frame.save(output_path)

                saved_count += 1
                observer.publish(
                    ProgressEvent(
                        event_type=ProgressEventType.RECORD_SAVED,
                        message=f"저장 완료: {output_path.name}",
                        current=saved_count,
                        total=total_sprites,
                        set_name=atlas_set.display_name,
                        current_atlas=str(atlas_path.name),
                        current_output=str(output_path),
                    )
                )

            processed_sets += 1
            observer.publish(
                ProgressEvent(
                    event_type=ProgressEventType.SET_COMPLETED,
                    message=f"세트 완료: {atlas_set.display_name}",
                    current=saved_count,
                    total=total_sprites,
                    set_name=atlas_set.display_name,
                )
            )

        observer.publish(
            ProgressEvent(
                event_type=ProgressEventType.COMPLETED,
                message="모든 파싱이 완료되었습니다.",
                current=saved_count,
                total=total_sprites,
                output_dir=request.output_dir,
            )
        )
        return ParseSummary(
            sets_processed=processed_sets,
            sprites_saved=saved_count,
            output_dir=request.output_dir,
            cancelled=False,
        )

    def _count_total_sprites(self, sets: list[AtlasSet]) -> int:
        total = 0
        for atlas_set in sets:
            raw = self._metadata_loader.load(atlas_set.info_path)
            total += len(raw.get("spath", []))
        return total

    @staticmethod
    def _validate_required_collections(atlas_set: AtlasSet, records, catalog) -> None:
        required = sorted({record.scollectionname for record in records})
        missing = [name for name in required if not catalog.contains(name)]
        if missing:
            available = ", ".join(sorted(path.stem for path in atlas_set.atlas_paths))
            raise ValueError(
                f"세트 '{atlas_set.display_name}' 에 필요한 아틀라스가 부족합니다. "
                f"누락: {missing} / 현재 PNG: {available}"
            )

    @staticmethod
    def _cancelled_summary(
        observer: ProgressObserver,
        output_dir: Path,
        processed_sets: int,
        saved_count: int,
        total_sprites: int,
    ) -> ParseSummary:
        observer.publish(
            ProgressEvent(
                event_type=ProgressEventType.CANCELLED,
                message="사용자 요청으로 작업이 취소되었습니다.",
                current=saved_count,
                total=total_sprites,
                output_dir=output_dir,
            )
        )
        return ParseSummary(
            sets_processed=processed_sets,
            sprites_saved=saved_count,
            output_dir=output_dir,
            cancelled=True,
        )
