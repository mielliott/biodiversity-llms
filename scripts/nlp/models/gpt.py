import os
import sys
import time
from typing import Any, Dict, Iterator
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice, ChatCompletionTokenLogprob
import tqdm
from torch.utils.data import DataLoader
from args import TokenScoresFormat
from .registry import ModelRegistry
from .model import Model
from .query import QueryDataset


@ModelRegistry.register("gpt")
class GPT(Model):
    def __init__(self):
        load_dotenv()
        self.params: Dict[str, Any] = {}
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name: str = "gpt-3.5-turbo-0125"

    def load_model(self):
        # OpenAI models are accessible through API
        pass

    def get_model_info(self) -> dict:
        return {"name": "GPT-3.5 Turbo", "version": "0125"}

    def set_parameters(self, params: Dict[str, Any]):
        self.params = params

        if "model_name" not in self.params:
            raise RuntimeError("Parameter --model_name not set")

        self.model_name = self.params["model_name"]

    def run(self, queries: Iterator[dict[str, str]]) -> Iterator[dict[str, Any]]:
        dataset = QueryDataset(queries)

        def custom_collate_fn(batch):
            return batch

        dataloader = DataLoader(
            dataset,
            batch_size=self.params.get("batch_size", 10),
            shuffle=False,
            collate_fn=custom_collate_fn,
        )

        question_number = 0
        for batch in tqdm.tqdm(dataloader, desc="Processing batches"):
            for inputs in batch:
                message = [{"role": "user", "content": inputs["query"]}]
                chat_completion = self.generate(
                    message,
                    n=self.params.get("num_responses"),
                    top_p=self.params.get("top_p"),
                    max_tokens=self.params.get("max_tokens"),
                    timeout=self.params.get("timeout"),
                    temperature=self.params.get("temperature"),
                )

                yield from self.process_results(question_number, inputs, chat_completion)
                question_number += 1

    def generate(self, message, **kwargs) -> ChatCompletion: # type: ignore[reportReturnType]
        max_retries = 3
        retry_delay_in_seconds = 5
        max_allowed_top_logprobs = 5

        for attempt in range(max_retries):
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
                print(
                    f"Request failed (attempt {attempt+1}/{max_retries}):",
                    e,
                    file=sys.stderr,
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay_in_seconds)
                else:
                    raise e

    def process_results(self, question_number: int, inputs: dict[str, Any], chat_completion: ChatCompletion) -> Iterator[dict[str, Any]]:
        for choice in chat_completion.choices:
            response_text, top_token_logprobs = self.process_chat_completion(choice, self.params["scores"])
            yield inputs | {
                "responses": response_text,
                "question number": question_number,
                "top tokens": list(top_token_logprobs.keys()),
                "top tokens logprobs": list(top_token_logprobs.values()),
                "input token count": chat_completion.usage.prompt_tokens, # type: ignore[reportOptionalMemberAccess]
                "output token count": chat_completion.usage.completion_tokens, # type: ignore[reportOptionalMemberAccess]
            }

    def process_chat_completion(self, chat_completion_choice: Choice, token_scores_format):
        match token_scores_format:
            case TokenScoresFormat.FIRST_TOKEN:
                first_token_data: ChatCompletionTokenLogprob = chat_completion_choice.logprobs.content[0] # type: ignore[reportOptionalMemberAccess]
                first_token_logprobs = {
                    top_logprob.token: top_logprob.logprob
                    for top_logprob in first_token_data.top_logprobs
                }
                return chat_completion_choice.message.content, first_token_logprobs

            case TokenScoresFormat.RESPONSE_TOKENS:
                response_token_logprobs = {
                    token_data.token: token_data.logprob
                    for token_data in chat_completion_choice.logprobs.content # type: ignore[reportOptionalMemberAccess]
                }
                return chat_completion_choice.message.content, response_token_logprobs
