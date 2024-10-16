
from typing import Dict, Any
from .models.registry import ModelRegistry
from .io import IOHandler

class ExperimentRunner:
    def __init__(self, model_category: str, params: Dict[str, Any]):
        self.model_class = ModelRegistry.get_model(model_category)
        if not self.model_class:
            raise ValueError(f"Model {model_category} not found in registry")
        self.model = self.model_class()
        self.model.set_parameters(params)
        self.model.load_model()

        self.ioHandler = IOHandler()

    def run_experiment(self, queries):
        results = self.model.run(queries)
        self.ioHandler.show(results)