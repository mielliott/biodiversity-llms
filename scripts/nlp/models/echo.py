from typing import Any, Dict, Iterable
from torch.utils.data import DataLoader
from .registry import ModelRegistry
from .model import Model
from .query import QueryDataset


@ModelRegistry.register("test")
class Echo(Model):
    def __init__(self, params: Dict[str, Any]):
        pass

    def load_model(self):
        pass

    def get_model_info(self) -> dict:
        return {"name": "test"}

    def run(self, queries: Iterable[dict[str, str]]):
        for inputs in queries:
            response = f"Echoing query \"{inputs['query']}\""
            result = inputs | {"response": response}
            yield result
