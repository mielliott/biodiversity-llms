from models.llm import LLM
from openai import OpenAI
from openai.types.chat import ChatCompletion
from typing import Iterable
import os
import sys
import time
from dotenv import load_dotenv

class GPT(LLM):
    def __init__(self, model: str, max_tokens: int, timeout: int, top_p: float, **kwargs):
        load_dotenv()
        self.model = model
        self.client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
        self.timeout = timeout
        self.top_p = top_p
        self.max_tokens = max_tokens

    def run(self, queries: Iterable[tuple[str,str]], num_responses: int, combine_responses: bool, escape: bool):
        for i, (input, question) in enumerate(queries):
            # See https://platform.openai.com/docs/api-reference/chat/create
            response = self.query_openai(question, n=num_responses, top_p=self.top_p, max_tokens=self.max_tokens, timeout=self.timeout)
            answers = []
            top_token_probs = {}
            for choice in response.choices:
                if choice.message.content != None:
                    answers.append(str(choice.message.content))
                else:
                    answers.append("")
                for logprob in choice.logprobs.content:
                    for toplogprob in logprob.top_logprobs:
                        top_token_probs[toplogprob.token] = toplogprob.logprob

            if escape:
                if combine_responses:
                    answers = [repr(answers)]
                else:
                    answers = [repr(answer) for answer in answers]
            elif combine_responses:
                answers = [" ".join(answers)]

            for answer in answers:
                yield (
                    input,
                    {
                        "query": repr(question),
                        "responses": answer,
                        "input token count": response.usage.prompt_tokens,
                        "output token count": response.usage.completion_tokens,
                        "question number": i,
                        "top tokens": list(top_token_probs.keys()),
                        "top tokens logprobs": list(top_token_probs.values())
                    }
                )

    # For kwargs see https://platform.openai.com/docs/api-reference/chat/create
    def query_openai(self, query: str, **kwargs) -> ChatCompletion:
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
