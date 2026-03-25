from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.controller import AppController


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError


class StartParseCommand(Command):
    def __init__(self, controller: AppController) -> None:
        self._controller = controller

    def execute(self) -> None:
        self._controller.start_parse()


class CancelParseCommand(Command):
    def __init__(self, controller: AppController) -> None:
        self._controller = controller

    def execute(self) -> None:
        self._controller.cancel_parse()
