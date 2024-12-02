from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional

from args import Params


class Model(ABC):
    @abstractmethod
    def __init__(self, params: Params):
        pass

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def run(self, queries: Iterator[dict[str, Any]], batch_id: Optional[str] = None) -> Iterator[dict[str, Any]]:
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        pass
