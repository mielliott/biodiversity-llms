import os
import json
from typing import Any, Dict
from utils.file_like_object import FileLikeObject
from openai import OpenAI
from args import Params, BatchProcess, TokenScoresFormat
from .model import Model
from .registry import ModelRegistry

MAX_TOP_LOGPROBS = 5


def make_request_id(query: dict) -> str:
    return json.dumps({k: query[k] for k in ("query_number", "pattern_number")})


def parse_request_id(request_id: str) -> dict:
    return json.loads(request_id)


@ModelRegistry.register("batch_gpt")
class BatchGPT(Model):
    """
    --batch write
        Takes the usual query table.
        Outputs a single item {"batch_id": str}.

    --batch read
        Takes a single item {"batch_id": str}.
        Outputs a table with a "request_id" field instead of the original query fields, and the usual output fields.
    """

    def __init__(self, params: Params):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        match params.batch:
            case BatchProcess.WRITE:
                self.handler = BatchWriter(params)
            case BatchProcess.READ:
                self.handler = BatchReader(params)
            case BatchProcess.NONE:
                raise RuntimeError("Please specify --batch write or --batch read")

    def load_model(self):
        # OpenAI models are accessible through API
        pass

    def get_model_info(self):
        return {"name": "batch_gpt"}

    def run(self, queries):
        yield from self.handler.run(self.client, queries)


class BatchHandler():
    def run(self, client: OpenAI, queries):
        yield from []


class BatchWriter(BatchHandler):
    def __init__(self, params: Params) -> None:
        self.model_name = params.model_name
        self.timeout = params.timeout
        self.generation_args = {
            "temperature": params.temperature,
            "n": params.num_responses,
            "max_tokens": params.max_tokens,
            "top_p": params.top_p
        }

    def run(self, client: OpenAI, queries):
        requests = self.create_req_objects(queries)
        requests_byte_stream = FileLikeObject(requests)

        openai_file = client.files.create(file=requests_byte_stream, purpose="batch")

        openai_batch = client.batches.create(
            input_file_id=openai_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )

        yield {"batch_id": openai_batch.id}

    def create_req_objects(self, queries):
        for query in queries:
            request = {
                "custom_id": make_request_id(query),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": query["prompt"]
                        }
                    ],
                    "logprobs": True,
                    "top_logprobs": MAX_TOP_LOGPROBS,
                    **self.generation_args
                }
            }
            yield (json.dumps(request) + "\n").encode()


class BatchReader(BatchHandler):
    def __init__(self, params: Params) -> None:
        self.token_scores_format = params.scores

    def run(self, client: OpenAI, queries):
        batch_id = next(queries)["batch_id"]
        yield from self.read_batch(client, batch_id)

    def read_batch(self, client: OpenAI, batch_id):
        batch = client.batches.retrieve(batch_id)
        # handle batch status
        match batch.status:
            case "failed":
                raise RuntimeError(f"Batch failed: {batch.error_file_id}")
            case "in_progress":
                raise RuntimeError("Batch is still in progress")
            case "completed":
                if not batch.output_file_id:
                    raise RuntimeError("Batch is marked \"completed\" but results are missing")

                output_content = client.files.content(batch.output_file_id)
                for line in output_content.iter_lines():
                    query_response_data = json.loads(line)
                    query_number, pattern_number = parse_request_id(query_response_data["custom_id"])
                    chat_completion = query_response_data["response"]["body"]
                    for query_response in self.process_results(chat_completion):
                        yield {
                            "query_number": query_number,
                            "pattern_number": pattern_number,
                        } | query_response
            case _:
                raise NotImplementedError(f"Unexpected batch status \"{batch.status}\"")

    def process_results(self, chat_completion: Dict[str, Any]):
        for choice in chat_completion["choices"]:
            response_text, top_token_logprobs = self.process_chat_completion(choice, self.token_scores_format)
            yield {
                "responses": response_text,
                "top_tokens": [x[0] for x in top_token_logprobs],
                "top_tokens_logprobs": [x[1] for x in top_token_logprobs],
                "input_token_count": chat_completion["usage"]["prompt_tokens"],
                "output_token_count": chat_completion["usage"]["completion_tokens"],
            }

    def process_chat_completion(self, chat_completion_choice: Dict[str, Any], token_scores_format):
        match token_scores_format:
            case TokenScoresFormat.FIRST_TOKEN:
                first_token_data = chat_completion_choice["logprobs"]["content"][0]
                first_token_logprobs = [
                    (top_logprob["token"], top_logprob["logprob"])
                    for top_logprob in first_token_data["top_logprobs"]
                ]
                return chat_completion_choice["message"]["content"], first_token_logprobs

            case TokenScoresFormat.RESPONSE_TOKENS:
                response_token_logprobs = [
                    (token_data["token"], token_data["logprob"])
                    for token_data in chat_completion_choice["logprobs"]["content"]
                ]
                return chat_completion_choice["message"]["content"], response_token_logprobs

            case _:
                raise NotImplementedError(token_scores_format)
