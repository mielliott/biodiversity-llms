from abc import ABC, abstractmethod
from typing import Dict, Any, Iterable

class Model(ABC):
    @abstractmethod
    def load_model(self):
        pass
    
    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]):
        pass
    
    @abstractmethod
    def run(self, queries: Iterable[tuple[str,str]]):
        pass
    
    @abstractmethod
    def generate(self, query: str, **kwargs) -> list[str]:
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        pass

    @abstractmethod
    def process_results(self, results: list[dict]) -> dict:
        pass