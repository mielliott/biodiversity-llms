from torch.utils.data import IterableDataset


class QueryDataset(IterableDataset):
    def __init__(self, queries):
        self.queries = queries

    def __iter__(self):
        return self.queries
