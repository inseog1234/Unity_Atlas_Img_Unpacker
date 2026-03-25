from src.application.controller import AppController
from src.infrastructure.progress import QueueProgressObserver
from src.infrastructure.repositories import DiskAtlasLoader, JsonFileMetadataLoader
from src.infrastructure.task_runner import BackgroundTaskRunner
from src.services.atlas_catalog import AtlasCatalogFactory
from src.services.atlas_parser_service import AtlasParserService
from src.services.layout_strategy import StableCanvasLayoutStrategy
from src.services.record_factory import SpriteRecordFactory
from src.services.sprite_extractor import HollowKnightSpriteExtractor
from src.ui.main_window import MainWindow


def main() -> None:
    observer = QueueProgressObserver()
    runner = BackgroundTaskRunner()

    service = AtlasParserService(
        metadata_loader=JsonFileMetadataLoader(),
        atlas_loader=DiskAtlasLoader(),
        record_factory=SpriteRecordFactory(),
        extractor=HollowKnightSpriteExtractor(),
        layout_strategy=StableCanvasLayoutStrategy(),
        catalog_factory=AtlasCatalogFactory(),
    )

    controller = AppController(
        parser_service=service,
        task_runner=runner,
        progress_observer=observer,
    )

    app = MainWindow(controller=controller, progress_queue=observer.queue)
    app.run()


if __name__ == "__main__":
    main()
