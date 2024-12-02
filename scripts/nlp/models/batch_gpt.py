import io
import os
import time
import queue
import asyncio
import aiohttp
from aiohttp import ClientSession
import threading
from utils.async_stream import AsyncFileLikeObject
import json
from typing import Iterator, Any, Dict
from openai import OpenAI
from .model import Model
from .registry import ModelRegistry
from args import Params, BatchProcess, TokenScoresFormat
from utils.stream import to_file_like_obj


class RunStatus:
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
            self.loop = asyncio.get_event_loop()
            self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
            self.item_queue = asyncio.Queue()
            self.run_status = RunStatus()
            self.thread.start()
            asyncio.run_coroutine_threadsafe(self.create_batch(queries, self.item_queue, self.run_status), self.loop)
            for item in self.wrap_async_iter(self.flush_queue(self.item_queue, self.run_status), self.loop):
                if item["request id"] == 'response':
                    continue
                yield item
        else:
            # read batch file
            yield from self.read_batch(queries, batch_id)

    async def create_req_object(self, queries, queue):
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
            await queue.put((f"request-{idx}", query))
            # .jsonl format (newline is required)
            yield (json.dumps(request) + '\n').encode()

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

    async def upload_to_openai(self, file_like_obj, queue, run_status_obj):
        url = 'https://api.openai.com/v1/files'
        headers = {
            'Authorization': 'Bearer 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'
        }

        async with ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('purpose', 'batch')
            data.add_field('file', file_like_obj, filename='batch.jsonl')
            async with session.post(url, headers=headers, data=data) as response:
                run_status_obj.running = False
                return await response.json()

    async def flush_queue(self, queue, run_status_obj):
        while run_status_obj.running:
            item = await queue.get()
            print('flush item type: ', type(item[1]))
            if len(item) > 2:
                yield {
                    "x": item[1]["x"],
                    "query": item[1]["query"],
                    "batch id": str(item[2]),
                    "request id": str(item[0]),
                }
            else:
                yield {
                    "x": item[1]["x"],
                    "query": item[1]["query"],
                    "batch id": "",
                    "request id": str(item[0]),
                }

    async def create_batch(self, data, queue, run_status_obj):
        objects = self.create_req_object(data, queue)
        file = AsyncFileLikeObject(objects)
        file_data = file.read()
        response = await self.upload_to_openai(file_data, queue, run_status_obj)
        print(response['id'])

        job = self.client.batches.create(
            input_file_id=response['id'],
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        await queue.put(("", {"x": "", "query": ""}, str(job.id)))
        return job

    def read_batch(self, queries, batch_id):
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
                # output dict -> custom_id: response
                responses = {}
                for line in output_content.iter_lines():
                    line = json.loads(line)
                    responses[line["custom_id"]] = line['response']['body']

                for query in queries:
                    chat_completion_response = responses[query["request id"]]
                    # remove batch id and request id from query
                    del query["batch id"]
                    del query["request id"]
                    yield from self.process_results(question_number, query, chat_completion_response)
                    question_number += 1

    def process_results(self, question_number: int, inputs: dict[str, Any], chat_completion: Dict[str, Any]) -> Iterator[dict[str, Any]]:
        for choice in chat_completion['choices']:
            response_text, top_token_logprobs = self.process_chat_completion(choice, self.token_scores_format)
            yield inputs | {
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
