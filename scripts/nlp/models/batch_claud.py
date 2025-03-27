import json

import anthropic

from utils.file_like_object import FileLikeObject
from args import Params, BatchProcess
from .model import Model
from .registry import ModelRegistry


def make_request_id(query: dict) -> str:
    return json.dumps({k: query[k] for k in ("query_number", "pattern_number")})


def parse_request_id(request_id: str) -> tuple[int, int]:
    data = json.loads(request_id)
    return data["query_number"], data["pattern_number"]


@ModelRegistry.register("batch_claud")
class BatchClaud(Model):
    def __init__(self, params: Params):
        self.client = anthropic.Anthropic()
        match params.batch:
            case BatchProcess.WRITE:
                self.handler = BatchWriter(params)
            case BatchProcess.READ:
                self.handler = BatchReader(params)
            case BatchProcess.NONE:
                raise RuntimeError("Please specify --batch write or --batch read")
        pass

    def load_model(self):
        pass
    
    def get_model_info(self):
        return {"name": "batch_claud"}
    
    def run(self, queries):
        yield from self.handler.run(self.client, queries)


class BatchHandler():
    def run(self, client, queries):
        yield from []


class BatchWriter(BatchHandler):
    def __init__(self, params: Params):
        self.model_name = params.model_name

        """
        Does not support logprobs
        Argument Reference: https:// docs.anthropic.com/en/api/messages
        """
        self.generation_args = {}
        if params.max_tokens is not None:
            self.generation_args["max_tokens"] = params.max_tokens
        if params.temperature is not None:
            self.generation_args["temperature"] = params.temperature
        if params.top_p is not None:
            self.generation_args["top_p"] = params.top_p

        self.timeout = params.timeout


    def create_req_objects(self, queries):
        for query in queries:
            request = {
                "custom_id": f"{make_request_id(query)}",
                "params": {
                    "model": self.model_name,
                    "messages": [{
                        "role": "user",
                        "content": query["prompt"]
                    }],
                    **self.generation_args
                }
            }
            print('request: ', request)
            yield (json.dumps(request) + "\n").encode()

    
    def run(self, client, queries):
        requests = self.create_req_objects(queries)
        requests_byte_stream = FileLikeObject(requests)
        claud_batch = client.messages.create(requests=requests_byte_stream)
        yield {"batch_id": claud_batch.id}

    
class BatchReader(BatchHandler):
    def __init__(self, params: Params):
        self.token_scores_format = params.scores

    
    def run(self, client: anthropic.Anthropic, queries):
        for query in queries:
            batch_id = query["batch_id"]
            yield from self.read_batch(client, batch_id)

        
    def read_batch(self, client: anthropic.Anthropic, batch_id):
        batch = client.batches.retrieve(batch_id)
        match batch.processing_status:
            case "in_progress": 
                raise RuntimeError("Batch job is still in progress")
            case "canceling":
                raise RuntimeError("Batch job is being canceled")
            case "ended":
                for line in client.messages.batches.results(batch_id):
                    query_response_data = json.loads(line)
                    query_number, pattern_number = parse_request_id(query_response_data["custom_id"])
                    chat_completion = query_response_data["message"]
                    yield {
                        "batch_id": batch_id,
                        "query_number": query_number,
                        "pattern_number": pattern_number,
                        "responses": chat_completion["content"]["text"],
                        "top_tokens": [],
                        "top_tokens_log_probs": [],
                        "input_token_count": chat_completion["usage"]["input_tokens"],
                        "output_token_count": chat_completion["usage"]["output_tokens"]
                    }
            case _:
                raise RuntimeError(f"Batch job failed: {batch.processing_status}")
