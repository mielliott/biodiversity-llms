import io
import os
import time
import json
from typing import Iterator, Any, Dict
from openai import OpenAI
from .model import Model
from .registry import ModelRegistry
from args import Params, BatchProcess, TokenScoresFormat
from utils.stream import to_file_like_obj


@ModelRegistry.register("batch_gpt")
class BatchGPT(Model):
    def __init__(self, params: Params):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.model_name = params.model_name
        self.num_responses = params.num_responses
        self.top_p = params.top_p
        self.max_tokens = params.max_tokens
        self.timeout = params.timeout
        self.temperature = params.temperature
        self.batch = params.batch
        self.token_scores_format = params.scores

    def load_model(self):
        # OpenAI models are accessible through API
        pass

    def get_model_info(self):
        return {"name": self.model_name}

    def run(self, queries):
        if self.batch is BatchProcess.WRITE:
            yield from self.create_batch(queries)
        else:
            #     # read batch file
            yield from self.read_batch(None)

    def create_req_object(self, queries):
        max_allowed_top_logprobs = 5
        for idx, query in enumerate(queries):
            request = {
                "custom_id": f"request-{idx}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": query['query']
                        }
                    ],
                    "temperature": self.temperature,
                    "n": self.num_responses,
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "logprobs": True,
                    "top_logprobs": max_allowed_top_logprobs
                }
            }
            # .jsonl format (newline is required)
            yield (json.dumps(request) + '\n').encode()

    def create_batch(self, queries):
        request_objects = self.create_req_object(queries)
        file = to_file_like_obj(request_objects)
        data = file.read()
        batch_file = self.client.files.create(
            file=data,
            purpose="batch"
        )
        job = self.client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        # yield query | {
        #     "batch id": self.batch_id,
        #     "request id": f"request-{idx}"
        # }
        yield {"batch id": job.id}

    def read_batch(self, batch_id):
        batch_id = "batch_673b766ad57c819081d67d2ded69c944"
        batch = self.client.batches.retrieve(batch_id)
        # handle batch status
        if batch.status == "failed":
            raise Exception(f"Batch failed: {batch.error_file_id}")
        elif batch.status == "in_progress":
            raise Exception("Batch is still in progress")
        elif batch.status == "completed":
            if batch.output_file_id:
                output_content = self.client.files.content(batch.output_file_id)
                question_number = 0
                for line in output_content.iter_lines():
                    chat_completion_response = json.loads(line)['response']['body']
                    yield from self.process_results(question_number, chat_completion_response)
                    question_number += 1

    def process_results(self, question_number: int, chat_completion: Dict[str, Any]) -> Iterator[dict[str, Any]]:
        for choice in chat_completion['choices']:
            response_text, top_token_logprobs = self.process_chat_completion(choice, self.token_scores_format)
            yield {
                "responses": response_text,
                "question number": question_number,
                "top tokens": [x[0] for x in top_token_logprobs],
                "top tokens logprobs": [x[1] for x in top_token_logprobs],
                "input token count": chat_completion['usage']['prompt_tokens'],
                "output token count": chat_completion['usage']['completion_tokens'],
            }

    def process_chat_completion(self, chat_completion_choice: Dict[str, Any], token_scores_format):
        match token_scores_format:
            case TokenScoresFormat.FIRST_TOKEN:
                first_token_data = chat_completion_choice['logprobs']['content'][0]
                first_token_logprobs = [
                    (top_logprob['token'], top_logprob['logprob'])
                    for top_logprob in first_token_data['top_logprobs']
                ]
                return chat_completion_choice['message']['content'], first_token_logprobs

            case TokenScoresFormat.RESPONSE_TOKENS:
                response_token_logprobs = [
                    (token_data['token'], token_data['logprob'])
                    for token_data in chat_completion_choice['logprobs']['content']
                ]
                return chat_completion_choice['message']['content'], response_token_logprobs

            case _:
                raise NotImplementedError(token_scores_format)
