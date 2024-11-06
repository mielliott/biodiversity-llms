import os
import sys
import time
from typing import Any, Dict, Iterator
from dotenv import load_dotenv
from openai import OpenAI
import tqdm
from torch.utils.data import DataLoader
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
                api_response = self.generate(
                    message,
                    n=self.params.get("num_responses"),
                    top_p=self.params.get("top_p"),
                    max_tokens=self.params.get("max_tokens"),
                    timeout=self.params.get("timeout"),
                    temperature=self.params.get("temperature"),
                )

                yield from self.process_results(question_number, inputs, api_response)
                question_number += 1

    def generate(self, message, **kwargs):
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                api_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=message,
                    logprobs=True,
                    top_logprobs=2,
                    **kwargs,
                )
                return api_response
            except Exception as e:
                print(
                    f"Request failed (attempt {attempt+1}/{max_retries}):",
                    e,
                    file=sys.stderr,
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e

    def process_results(self, question_number: int, inputs: dict[str, Any], responses):
        answers = []
        all_top_token_probs = []
        for response in responses.choices:
            answers.append(str(response.message.content or ""))
            top_token_probs = {
                toplogprob.token: toplogprob.logprob
                for logprob in response.logprobs.content
                for toplogprob in logprob.top_logprobs
            }
            all_top_token_probs.append(top_token_probs)

        if self.params.get("escape_responses", False):
            answers = (
                [repr(answers)]
                if self.params.get("combine_responses", False)
                else [repr(answer) for answer in answers]
            )
        elif self.params.get("combine_responses", False):
            answers = [" ".join(answers)]

        for answer, top_token_probs in zip(answers, all_top_token_probs):
            yield inputs | {
                "responses": answer.replace("\n", " ").replace("\t", " "),
                "question number": question_number,
                "top tokens": list(top_token_probs.keys()),
                "top tokens logprobs": list(top_token_probs.values()),
                "input token count": responses.usage.prompt_tokens,
                "output token count": responses.usage.completion_tokens,
            }
