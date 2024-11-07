from typing import Any
from torch.utils.data import IterableDataset


class QueryDataset(IterableDataset):
    def __init__(self, queries):
        self.queries = queries

    def __iter__(self):
        return self.queries

    def __getitem__(self, index) -> Any:
        raise NotImplementedError("Random access is not permitted on streamed datasets")
