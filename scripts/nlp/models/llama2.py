from models.llm import LLM
from transformers import AutoTokenizer, AutoModelForCausalLM

class Llama2(LLM):
    def __init__(self, model: str, top_k: float, api_access_key: str, **kwargs):
        self.top_k = top_k
        self.tokenizer = AutoTokenizer.from_pretrained(model, token=api_access_key)
        self.model = AutoModelForCausalLM.from_pretrained(model, token=api_access_key, device_map="auto")
        self.model.tie_weights()

    def run(self, header: str, questions, max_tokens: int, num_responses: int, combine_responses: bool, escape: bool):
        for i, (input, question) in enumerate(questions):
            token_scores, token_strings = self.query_llama2(question)
            yield (
                input,
                {
                    "query": repr(question),
                    "top k token strings": repr(token_strings),
                    "top k token scores": repr(token_scores),
                    "question number": i
                }
            )
    
    def query_llama2(self, query: str, **kwargs):
        input_ids = self.tokenizer([query], return_tensors="pt").input_ids.to("cuda")
        outputs = self.model.generate(input_ids, max_length=30, return_dict_in_generate=True, output_scores=True)

        # completion = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)

        top_k = outputs.scores[-1][0].topk(self.top_k)
        top_k_token_scores = top_k.values.tolist()
        top_k_token_strings = [self.tokenizer.decode(t) for t in top_k.indices]
        return (
            top_k_token_scores,
            top_k_token_strings
        )
