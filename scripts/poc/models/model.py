from abc import ABC, abstractmethod
from typing import Dict, Any

class Model(ABC):
    @abstractmethod
    def load_model(self):
        pass
    
    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]):
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