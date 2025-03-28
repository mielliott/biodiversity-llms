import os
import sys
import time
from typing import Any, Iterator, Optional
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_token_logprob import ChatCompletionTokenLogprob
import tqdm
from torch.utils.data import DataLoader
from args import Params, TokenScoresFormat
from .registry import ModelRegistry
from .model import Model
from .query import QueryDataset


@ModelRegistry.register("gpt")
class GPT(Model):
    def __init__(self, params: Params):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.batch_size = params.batch_size
        self.model_name = params.model_name
        self.num_responses = params.num_responses
        self.top_p = params.top_p
        self.max_tokens = params.max_tokens
        self.timeout = params.timeout
        self.temperature = params.temperature
        self.token_scores_format = params.scores
        self.batch_size = params.batch_size

    def load_model(self):
        # OpenAI models are accessible through API
        pass

    def get_model_info(self) -> dict:
        return {"name": self.model_name}

    def run(self, queries: Iterator[dict[str, Any]], batch_id: Optional[str] = None) -> Iterator[dict[str, Any]]:
        dataset = QueryDataset(queries)

        def custom_collate_fn(batch):
            return batch

        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            collate_fn=custom_collate_fn,
        )

        for batch in tqdm.tqdm(dataloader, desc="Processing batches"):
            for query in batch:
                message = [{"role": "user", "content": query["prompt"]}]
                chat_completion = self.generate(
                    message,
                    n=self.num_responses,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    temperature=self.temperature,
                )

                yield from self.process_results(query, chat_completion)

    def generate(self, message, **kwargs) -> ChatCompletion:
        max_retries = 3
        retry_delay_in_seconds = 5
        max_allowed_top_logprobs = 5

        attempt = 0
        while True:
            try:
                chat_completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=message,
                    logprobs=True,
                    top_logprobs=max_allowed_top_logprobs,
                    **kwargs,
                )
                return chat_completion
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}):", e, file=sys.stderr)
                if attempt < max_retries - 1:
                    attempt += 1
                    time.sleep(retry_delay_in_seconds)
                else:
                    raise e

    def process_results(self, inputs: dict[str, Any], chat_completion: ChatCompletion) -> Iterator[dict[str, Any]]:
        for choice in chat_completion.choices:
            response_text, top_token_logprobs = self.process_chat_completion(choice, self.token_scores_format)
            yield inputs | {
                "responses": response_text,
                "top_tokens": [x[0] for x in top_token_logprobs],
                "top_tokens_logprobs": [x[1] for x in top_token_logprobs],
                "input_token_count": chat_completion.usage.prompt_tokens,  # type: ignore[reportOptionalMemberAccess]
                "output_token_count": chat_completion.usage.completion_tokens,  # type: ignore[reportOptionalMemberAccess]
            }

    def process_chat_completion(self, chat_completion_choice: Choice, token_scores_format):
        match token_scores_format:
            case TokenScoresFormat.FIRST_TOKEN:
                first_token_data: ChatCompletionTokenLogprob = chat_completion_choice.logprobs.content[0]  # type: ignore[reportOptionalMemberAccess]
                first_token_logprobs = [
                    (top_logprob.token, top_logprob.logprob)
                    for top_logprob in first_token_data.top_logprobs
                ]
                return chat_completion_choice.message.content, first_token_logprobs

            case TokenScoresFormat.RESPONSE_TOKENS:
                response_token_logprobs = [
                    (token_data.token, token_data.logprob)
                    for token_data in chat_completion_choice.logprobs.content  # type: ignore[reportOptionalMemberAccess]
                ]
                return chat_completion_choice.message.content, response_token_logprobs

            case _:
                raise NotImplementedError(token_scores_format)
