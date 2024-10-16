from torch.utils.data import Dataset
from typing import List

class Queries(Dataset):
    def __init__(self, queries):
        self.queries = queries
        
    def __len__(self):
        return len(self.queries)
    
    def __getitem__(self, idx):
        return self.queries[idx]
    