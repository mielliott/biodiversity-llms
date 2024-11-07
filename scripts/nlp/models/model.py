from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator


class Model(ABC):
    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]):
        pass

    @abstractmethod
    def run(self, queries: Iterator[dict[str, str]]) -> Iterator[dict[str, Any]]:
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        pass
