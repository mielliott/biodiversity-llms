
from typing import Dict, Any
from .models.registery import ModelRegistry
from .io import IOHandling

class ExperimentRunner:
    def __init__(self, model_name: str, params: Dict[str, Any]):
        self.params = params

        self.model_class = ModelRegistry.get_model(model_name)
        if not self.model_class:
            print(ModelRegistry.list_models())
            raise ValueError(f"Model {model_name} not found in registry")
        self.model = self.model_class()
        self.model.load_model()
        self.model.set_parameters(params)

        self.ioHandler = IOHandling()

    def run_experiment(self, queries):
        results = self.model.run(queries)
        self.ioHandler.show(results)