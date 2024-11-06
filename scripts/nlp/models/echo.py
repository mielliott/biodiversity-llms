from typing import Any, Dict, Iterable
from torch.utils.data import DataLoader
from .registry import ModelRegistry
from .model import Model
from .query import QueryDataset


@ModelRegistry.register("test")
class Echo(Model):
    def __init__(self):
        self.params: dict[str, Any] = {}

    def load_model(self):
        pass

    def get_model_info(self) -> dict:
        return {"name": "test"}

    def set_parameters(self, params: Dict[str, Any]):
        self.params = params

    def run(self, queries: Iterable[dict[str, str]]):
        dataset = QueryDataset(queries)

        def custom_collate_fn(batch):
            return batch

        dataloader = DataLoader(
            dataset,
            batch_size=self.params.get("batch_size", 10),
            shuffle=False,
            collate_fn=custom_collate_fn,
        )

        for batch in dataloader:
            for inputs in batch:
                response = f"Echoing query \"{inputs['query']}\""
                result = inputs | {"response": response}
                yield result
