import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI
from typing import Any, Dict, Iterable
from .registery import ModelRegistry
from .model import Model

@ModelRegistry.register("gpt-3.5-turbo-0125")
class GPT(Model):
    def __init__(self):
        load_dotenv()
        self.params: Dict[str, Any] = {}
        self.client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
        self.model: str = "gpt-3.5-turbo-0125"

    def load_model(self):
        # OpenAI models are accessible through API
        pass

    def get_model_info(self) -> dict:
        return {"name": "GPT-3.5 Turbo", "version": "0125"}
    
    def set_parameters(self, params: Dict[str, Any]):
        self.params = params
        
    def run(self, queries: Iterable[tuple[str,str]]):

        for idx, (input, query) in enumerate(queries):
            response = self.generate(query, n=self.params.get('num_responses', 1), top_p=self.params.get('top_p'), max_tokens=self.params.get('max_tokens'), timeout=self.params.get('timeout'))

            return self.process_results(idx, input, query, response)
    
    def generate(self, query, **kwargs):
        print('self.params: ', kwargs)
        
        while (True):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": query}],
                    logprobs=True,
                    top_logprobs=2,
                    **kwargs
                )
                return response
            except Exception as e:
                print("Request failed:", e, file=sys.stderr)
                time.sleep(5)
        
    def process_results(self, idx, input, query, response):
        answers = [
            str(choice.message.content or "") 
            for choice in response.choices
        ]
        top_token_probs = {
            toplogprob.token: toplogprob.logprob
            for choice in response.choices
            for logprob in choice.logprobs.content
            for toplogprob in logprob.top_logprobs
        }

        if self.params.get('escape_responses', False):
            answers = [repr(answers)] if self.params.get('combine_responses', False) else [repr(answer) for answer in answers ]
        elif self.params.get('combine_responses', False):
            answers = [" ".join(answers)]
        for answer in answers:
            yield (input, {
            "query": repr(query),
            "responses": answer,
            "question number": idx,
            "top tokens": list(top_token_probs.keys()),
            "top tokens logprobs": list(top_token_probs.values()),
            # not specific to the response of the question - llm specific information.
            "input token count": response.usage.prompt_tokens,
            "output token count": response.usage.completion_tokens,
        })
