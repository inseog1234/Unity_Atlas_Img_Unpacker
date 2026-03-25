from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from src.domain.entities import AtlasSet, ParseRequest
from src.domain.events import ProgressEvent, ProgressEventType
from src.domain.interfaces import ParserService
from src.infrastructure.progress import QueueProgressObserver
from src.infrastructure.task_runner import BackgroundTaskRunner


class AppController:
    def __init__(
        self,
        parser_service: ParserService,
        task_runner: BackgroundTaskRunner,
        progress_observer: QueueProgressObserver,
    ) -> None:
        self._parser_service = parser_service
        self._task_runner = task_runner
        self._progress_observer = progress_observer
        self._sets: list[AtlasSet] = []
        self._output_dir: Optional[Path] = None

    @property
    def sets(self) -> list[AtlasSet]:
        return list(self._sets)

    @property
    def output_dir(self) -> Optional[Path]:
        return self._output_dir

    @property
    def is_running(self) -> bool:
        return self._task_runner.is_running

    def add_set_from_folder(self, folder_path: str) -> AtlasSet:
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"폴더가 없습니다: {folder}")
        if not folder.is_dir():
            raise NotADirectoryError(f"폴더가 아닙니다: {folder}")

        info_path = folder / "SpriteInfo.json"
        if not info_path.exists():
            raise FileNotFoundError(f"SpriteInfo.json 이 없습니다: {info_path}")

        atlas_paths = tuple(sorted(p for p in folder.glob("*.png") if p.is_file()))
        if not atlas_paths:
            raise FileNotFoundError(f"PNG 파일이 없습니다: {folder}")

        atlas_set = AtlasSet(
            atlas_paths=atlas_paths,
            info_path=info_path,
            display_name=folder.parent.name if folder.name == "0.Atlases" else folder.name,
            source_dir=folder,
        )
        self._sets.append(atlas_set)
        return atlas_set

    def add_set_from_files(self, atlas_paths: Iterable[str], info_path: str) -> AtlasSet:
        atlas_list = tuple(sorted(Path(path) for path in atlas_paths))
        if not atlas_list:
            raise ValueError("PNG 파일을 하나 이상 선택하세요.")
        for atlas in atlas_list:
            if not atlas.exists():
                raise FileNotFoundError(f"이미지 파일이 없습니다: {atlas}")
            if atlas.suffix.lower() != ".png":
                raise ValueError(f"PNG 파일만 추가할 수 있습니다: {atlas}")

        info = Path(info_path)
        if not info.exists():
            raise FileNotFoundError(f"json 파일이 없습니다: {info}")
        if info.name.lower() != "spriteinfo.json" and info.suffix.lower() != ".json":
            raise ValueError("info 파일은 json 이어야 합니다.")

        source_dir = info.parent
        atlas_set = AtlasSet(
            atlas_paths=atlas_list,
            info_path=info,
            display_name=source_dir.parent.name if source_dir.name == "0.Atlases" else source_dir.name,
            source_dir=source_dir,
        )
        self._sets.append(atlas_set)
        return atlas_set

    def remove_set(self, set_id: str) -> None:
        self._sets = [atlas_set for atlas_set in self._sets if atlas_set.id != set_id]

    def clear_sets(self) -> None:
        self._sets.clear()

    def set_output_dir(self, output_dir: str) -> None:
        path = Path(output_dir)
        if not path.exists():
            raise FileNotFoundError(f"출력 폴더가 없습니다: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"출력 경로가 폴더가 아닙니다: {path}")
        self._output_dir = path

    def start_parse(self) -> None:
        if not self._sets:
            raise ValueError("파싱할 세트를 하나 이상 추가하세요.")
        if self._output_dir is None:
            raise ValueError("출력 폴더를 먼저 선택하세요.")
        if self._task_runner.is_running:
            raise RuntimeError("이미 파싱 중입니다.")

        request = ParseRequest(sets=self.sets, output_dir=self._output_dir)

        def task(cancel_event):
            try:
                self._parser_service.parse(request, cancel_event, self._progress_observer)
            except Exception as exc:  # noqa: BLE001
                self._progress_observer.publish(
                    ProgressEvent(
                        event_type=ProgressEventType.ERROR,
                        message="작업 중 오류가 발생했습니다.",
                        error_message=str(exc),
                    )
                )

        self._task_runner.run(task)

    def cancel_parse(self) -> None:
        self._task_runner.cancel()
