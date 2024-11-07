from abc import ABC, abstractmethod
from typing import Any, Iterator


class Model(ABC):
    @abstractmethod
    def __init__(self, params: dict[str, Any]):
        pass

    @abstractmethod
    def run(self, queries: Iterator[dict[str, str]]) -> Iterator[dict[str, Any]]:
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        pass
