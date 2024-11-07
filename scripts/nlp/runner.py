
from typing import Dict, Any, TextIO
from models.registry import ModelRegistry
from llm_io import IOHandler

class ExperimentRunner:
    def __init__(self, model_category: str, params: Dict[str, Any], io_handler: IOHandler):
        self.model_class = ModelRegistry.get_model(model_category)
        if not self.model_class:
            raise ValueError(f"Model {model_category} not found in registry")

        self.model = self.model_class()
        self.model.set_parameters(params)
        self.model.load_model()
        self.io_handler = io_handler

    def run_experiment(self, input_stream: TextIO, output_stream: TextIO):
        queries = self.io_handler.make_queries(input_stream)
        results = self.model.run(queries)
        self.io_handler.write_results(output_stream, results)
