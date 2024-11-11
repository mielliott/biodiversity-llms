from math import log
from random import choice, betavariate
from typing import Any, Iterable

from args import Params
from .registry import ModelRegistry
from .model import Model


def echo_response(inputs: dict[str, Any]):
    response = f"Echoing query \"{inputs['query']}\""
    return inputs | {"responses": response}


def yes_no_response(inputs: dict[str, Any]):
    prob = betavariate(1, 1)
    top_tokens = choice((["Yes", "No"], ["No", "Yes"]))
    return inputs | {"responses": top_tokens[0], "top tokens logprobs": [log(prob), log(1 - prob)]}


@ModelRegistry.register("test")
class Test(Model):
    def __init__(self, params: Params):
        match params.model_name:
            case "echo":
                self.response_generator = echo_response
            case "yes_no":
                self.response_generator = yes_no_response
            case _:
                raise RuntimeError(f"Bad test model name {params.model_name}")

    def load_model(self):
        pass

    def get_model_info(self) -> dict:
        return {"name": "test"}

    def run(self, queries: Iterable[dict[str, Any]]):
        for inputs in queries:
            yield self.response_generator(inputs)
