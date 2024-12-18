import os
import sys
import tqdm
from typing import Any, Iterator, Optional, List, Tuple
import torch
from torch import LongTensor
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoConfig,
    LlamaForCausalLM,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)
from transformers.generation.utils import GenerateOutput

from args import Params
from .registry import ModelRegistry
from .model import Model
from .query import QueryDataset


@ModelRegistry.register("llama")
class Llama(Model):
    model: PreTrainedModel
    tokenizer: PreTrainedTokenizerBase
    config: Any

    def __init__(self, params: Params):
        if not os.getenv("HF_TOKEN"):
            raise RuntimeError("Environment variable HF_TOKEN not set. Generate a token at https://huggingface.co/settings/tokens.")
        print("Using HuggingFace cache directory", os.getenv("HF_HOME"), file=sys.stderr)

        if params.model_name.startswith("/"):
            self.hf_model_path = params.model_name
            self.local_files_only = True
        else:
            self.hf_model_path = f"meta-llama/{params.model_name}"
            self.local_files_only = False

        self.batch_size = params.batch_size
        self.max_tokens = params.max_tokens
        self.num_responses = params.num_responses
        self.top_p = params.top_p
        self.top_k = params.top_k
        self.temperature = params.temperature

        self.precision = params.precision
        if self.precision is None:
            raise RuntimeError("--precision is required for Llama models")

    def get_model_info(self):
        return {
            "family": "llama",
            "version": "3.2-1b-Instruct",
            "name": self.hf_model_path,
            "provider": "Hugging Face",
            "device": self.model.device,
            "precision": self.precision,
        }

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.hf_model_path, local_files_only=self.local_files_only)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        self.config = AutoConfig.from_pretrained(self.hf_model_path, local_files_only=self.local_files_only)

        precision_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }

        torch_dtype = precision_map.get(self.precision)

        self.model = LlamaForCausalLM.from_pretrained(
            self.hf_model_path,
            device_map="auto",
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            local_files_only=self.local_files_only
        )

    def run(self, queries: Iterator[dict[str, Any]], batch_id: Optional[str] = None) -> Iterator[dict[str, Any]]:
        dataset = QueryDataset(queries)

        def custom_collate_fn(batch):
            return batch

        # TODO: check how to batch on the number of tokens here
        data_loader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            collate_fn=custom_collate_fn,
        )

        for batch_inputs in tqdm.tqdm(data_loader, desc="Processing batches"):
            prompts = [self.construct_prompt(inputs["query"]) for inputs in batch_inputs]
            input_tensors = self.tokenizer(prompts, return_tensors="pt", truncation=True, padding=True)

            input_details = [
                inputs | {"prompt": prompt, "tensor": tensor, "mask": mask}
                for inputs, prompt, tensor, mask in zip(batch_inputs, prompts, input_tensors.input_ids, input_tensors.attention_mask)
            ]
            # TODO: to enable multiple return sequences - turn on sampling and top_k should be passed as > 1 and write the process results function.
            # args = {"num_return_sequences": self.num_responses, "do_sample": True, num_beams = None} if self.num_responses > 1 else {}

            params = {}
            if self.top_k > 0:
                params["top_k"] = self.top_k
            responses = self.generate(input_tensors, **params)
            yield from self.process_results(input_details, responses)

    def generate(self, input_tensors, **kwargs) -> GenerateOutput | LongTensor:
        input_ids: torch.Tensor = input_tensors.input_ids
        attention_mask: torch.Tensor = input_tensors.attention_mask
        # + 10 buffer to accomodate special tokens
        max_new_tokens = self.max_tokens + 10
        with torch.no_grad():
            try:
                return self.model.generate(
                    input_ids=input_ids.to(self.model.device),
                    attention_mask=attention_mask.to(self.model.device),
                    max_new_tokens=max_new_tokens,
                    top_p=self.top_p,
                    temperature=self.temperature,
                    do_sample=False,
                    num_beams=1,
                    output_scores=True,
                    low_memory=True,
                    return_dict_in_generate=True,
                    **kwargs,
                )
            except RuntimeError as e:
                print(f"Error during generation: {e}")
                print(f"Input shape: {input_ids.shape}")
                print(f"Attention mask shape: {attention_mask.shape}")
                print(f"Device: {self.model.device}")
                raise

    def process_results(self, inputs: list[dict[str, Any]], outputs: GenerateOutput | LongTensor) -> Iterator[dict[str, Any]]:
        if isinstance(outputs, GenerateOutput):
            generated_sequences = outputs.sequences
            scores = outputs.scores
        else:
            raise TypeError("Expected outputs to be an instance of GenerateOutput")

        # TODO: enable multiple responses for future use
        for i, (input, seq, seq_scores) in enumerate(zip(inputs, generated_sequences, zip(*scores))):
            input_token_count = input['tensor'].shape[0]
            output_tokens, output_distributions = self.remove_special_tokens(seq[input_token_count:], list(seq_scores))
            response_text = self.tokenizer.decode(output_tokens, clean_up_tokenization_spaces=True)

            # Implement TokenScoresFormat to return one or all tokens scores
            top_tokens, top_tokens_logprobs = self.get_top_k_scores(output_distributions[0], 5)

            query = input['query']
            output_tokens_count = len(output_tokens)
            filtered_input = {k: v for k, v in input.items() if k not in ["prompt", "tensor", "mask"]}
            yield filtered_input | {
                "query": query,
                "responses": response_text,
                "top tokens": top_tokens,
                "top tokens logprobs": top_tokens_logprobs,
                "input token count": input_token_count,
                "output token count": output_tokens_count,
            }

    def construct_prompt(self, query: str) -> str:
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Based on your knowledge, answer the question with either "Yes" or "No" response.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{query}<|eot_id|>"""

    ''' 
    References:
    https://github.com/meta-llama/llama3/issues/77#issuecomment-2067393063
    https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1
    '''

    def remove_special_tokens(self, output_tokens: torch.Tensor, output_scores: list[torch.Tensor]) -> Tuple[List[int], List[torch.Tensor]]:
        # special_tokens =['\n', '\n\n', 'assistant', '.']
        special_tokens = [271, 198, 78191, 13]
        tokens = []
        scores = []

        for token, score in zip(output_tokens, output_scores):
            if (token <= 128000) and (token not in special_tokens):
                tokens.append(token)
                scores.append(score)

        return tokens, scores

    def get_top_k_scores(self, distribution: torch.Tensor, k: int) -> Tuple[List[str], List[float]]:
        log_probs = torch.log(torch.softmax(distribution, dim=-1))
        top_log_probs, top_indices = log_probs.topk(k, dim=-1, sorted=True)
        top_tokens = [self.tokenizer.decode([idx.item()]) for idx in top_indices]
        top_tokens_logprobs = top_log_probs.tolist()
        return top_tokens, top_tokens_logprobs
