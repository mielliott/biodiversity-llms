import os
import queue
import threading
import json
from typing import Iterator, Any, Dict
import asyncio
import aiohttp
from aiohttp import ClientSession
from utils.async_stream import AsyncFileLikeObject
from openai import OpenAI
from args import Params, BatchProcess, TokenScoresFormat
from .model import Model
from .registry import ModelRegistry


class RunState:
    running = True


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

    def run(self, queries, batch_id=None):
        if self.batch is BatchProcess.WRITE:
            loop = asyncio.get_event_loop()
            thread = threading.Thread(target=loop.run_forever, daemon=True)
            query_buffer = asyncio.Queue()
            run_status = RunState()
            thread.start()
            asyncio.run_coroutine_threadsafe(self.create_batch(queries, query_buffer, run_status), loop)
            for query in self.wrap_async_iter(self.flush_queue(query_buffer, run_status), loop):
                if query["request_id"] == "response":
                    continue
                yield query
        else:
            # read batch file
            yield from self.read_batch(queries, batch_id)

    async def create_req_objects(self, queries, query_buffer):
        max_allowed_top_logprobs = 5
        for i, query in enumerate(queries):
            request = {
                "custom_id": f"request-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": query["query"]
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
            await query_buffer.put((f"request-{i}", query))
            # .jsonl format (newline is required)
            yield (json.dumps(request) + "\n").encode()

    # Refer: https://stackoverflow.com/a/55164899
    def wrap_async_iter(self, ait, loop):
        """Wrap an asynchronous iterator into a synchronous one"""
        q = queue.Queue()
        _END = object()

        async def aiter_to_queue():
            try:
                async for item in ait:
                    q.put(item)
            finally:
                q.put(_END)

        def yield_queue_items():
            while True:
                next_item = q.get()
                if next_item is _END:
                    break
                yield next_item
            # After observing _END we know the aiter_to_queue coroutine has
            # completed.  Invoke result() for side effect - if an exception
            # was raised by the async iterator, it will be propagated here.
            async_result.result()

        async_result = asyncio.run_coroutine_threadsafe(aiter_to_queue(), loop)
        return yield_queue_items()

    async def upload_to_openai(self, file_data, run_status: RunState):
        url = "https://api.openai.com/v1/files"
        headers = {
            "Authorization": "Bearer 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"
        }

        async with ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("purpose", "batch")
            data.add_field("file", file_data, filename="batch.jsonl")
            async with session.post(url, headers=headers, data=data) as response:
                run_status.running = False
                return await response.json()

    async def flush_queue(self, query_buffer, run_status):
        while run_status.running:
            query = await query_buffer.get()
            if len(query) > 2:
                yield {
                    "x": query[1]["x"],
                    "query": query[1]["query"],
                    "batch_id": str(query[2]),
                    "request_id": str(query[0]),
                }
            else:
                yield {
                    "x": query[1]["x"],
                    "query": query[1]["query"],
                    "batch_id": "",
                    "request_id": str(query[0]),
                }

    async def create_batch(self, data, query_buffer, run_state):
        objects = self.create_req_objects(data, query_buffer)
        file = AsyncFileLikeObject(objects)
        file_data = file.read()
        response = await self.upload_to_openai(file_data, run_state)

        job = self.client.batches.create(
            input_file_id=response["id"],
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        await query_buffer.put(("", {"x": "", "query": ""}, str(job.id)))
        return job

    def read_batch(self, queries, batch_id):
        batch = self.client.batches.retrieve(batch_id)
        # handle batch status
        match batch.status:
            case "failed":
                raise RuntimeError(f"Batch failed: {batch.error_file_id}")
            case "in_progress":
                raise RuntimeError("Batch is still in progress")
            case "completed":
                if not batch.output_file_id:
                    raise RuntimeError("Batch is marked \"completed\" but results are missing")

                output_content = self.client.files.content(batch.output_file_id)
                # output dict -> custom_id: response
                responses = {}
                for line in output_content.iter_lines():
                    line = json.loads(line)
                    responses[line["custom_id"]] = line["response"]["body"]

                for query in queries:
                    chat_completion_response = responses[query["request_id"]]
                    # remove batch_id and request_id from query
                    del query["batch_id"]
                    del query["request_id"]
                    yield from self.process_results(query, chat_completion_response)
            case _:
                raise NotImplementedError(f"Unexpected batch status \"{batch.status}\"")

    def process_results(self, inputs: dict[str, Any], chat_completion: Dict[str, Any]) -> Iterator[dict[str, Any]]:
        for choice in chat_completion["choices"]:
            response_text, top_token_logprobs = self.process_chat_completion(choice, self.token_scores_format)
            yield inputs | {
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
