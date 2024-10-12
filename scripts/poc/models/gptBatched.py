import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI
from typing import Any, Dict, List, Tuple
import tqdm
from torch.utils.data import Dataset, DataLoader
from .registry import ModelRegistry
from .model import Model
from .query import Queries

@ModelRegistry.register("gpt-batch-3.5-turbo-0125")
class GPTBatched(Model):
    def __init__(self):
        load_dotenv()
        self.params: Dict[str, Any] = {}
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model: str = "gpt-3.5-turbo-0125"

    def load_model(self):
        # OpenAI models are accessible through API
        pass

    def get_model_info(self) -> dict:
        return {"name": "GPT-3.5 Turbo", "version": "0125"}
    
    def set_parameters(self, params: Dict[str, Any]):
        self.params = params
        
    def run(self, queries: List[Tuple[str, str]]):
        dataset = Queries(queries)
        def custom_collate_fn(batch):
            return batch

        dataloader = DataLoader(
            dataset, 
            batch_size=self.params.get('batch_size', self.params.get('batch_size', 10)), 
            shuffle=False,
            collate_fn=custom_collate_fn
        )

        questionNumber = 0
        batch_results = []
        for batch in tqdm.tqdm(dataloader, desc="Processing batches"):
            if len(batch) < 2:
                inputs, queries = batch[0]
                queries = [queries]
                inputs = [inputs]
            else: 
                inputs, queries = zip(*batch)

            for input, query in zip(inputs,queries):
                message = [{"role": "user", "content": query}]
                response = self.generate(
                    message, 
                    n=self.params.get('num_responses', 1), 
                    top_p=self.params.get('top_p'), 
                    max_tokens=self.params.get('max_tokens'),
                    timeout=self.params.get('timeout')
                )
                batch_results.extend(self.process_results(questionNumber,[input], [query], response))
                questionNumber += 1

        return batch_results
    
    def generate(self, message: List[str], **kwargs):
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=message,
                    logprobs=True,
                    top_logprobs=2,
                    **kwargs
                )
                return response
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}):", e, file=sys.stderr)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e
        
    def process_results(self, idx: int, inputs: List[str], queries: List[str], responses):
        results = []
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

        if self.params.get('escape_responses', False):
            answers = [repr(answers)] if self.params.get('combine_responses', False) else [repr(answer) for answer in answers]
        elif self.params.get('combine_responses', False):
            answers = [" ".join(answers)]

        for answer, top_token_probs in zip(answers, all_top_token_probs):
            results.append({
                "input": inputs[0],
                "query": repr(queries[0]),
                "responses": answer,
                "question number": idx,
                "top tokens": list(top_token_probs.keys()),
                "top tokens logprobs": list(top_token_probs.values()),
                "input token count": responses.usage.prompt_tokens,
                "output token count": responses.usage.completion_tokens
            })
        return results