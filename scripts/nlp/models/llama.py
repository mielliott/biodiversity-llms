import os
from typing import Dict, Any, Iterator
from dotenv import load_dotenv
import torch
from transformers import (
    AutoTokenizer,
    AutoConfig,
    LlamaForCausalLM,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)
from torch.utils.data import DataLoader
import tqdm
from .registry import ModelRegistry
from .model import Model
from .query import QueryDataset


@ModelRegistry.register("llama")
class Llama(Model):
    model_name: str
    model: PreTrainedModel
    tokenizer: PreTrainedTokenizerBase
    config: Any

    def __init__(self):
        load_dotenv(override=True, verbose=True)
        self.params: Dict[str, Any] = {}

        if not os.getenv("HF_TOKEN"):
            raise RuntimeError("Environment variable HF_TOKEN not defined. Generate a token at https://huggingface.co/settings/tokens.")

        print("Using HuggingFace cache directory", os.getenv("HF_HOME"))

    def get_model_info(self) -> dict:
        return {
            "family": "llama",
            "version": "3.2-1b-Instruct",
            "name": self.model_name,
            "provider": "Hugging Face",
            "device": self.model.device,
            "precision": self.params.get("precision"),
        }

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        self.config = AutoConfig.from_pretrained(self.model_name)

        precision_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }

        precision = self.params.get("precision")
        if precision is None:
            raise RuntimeError("--precision is required for Llama models")

        torch_dtype = precision_map.get(precision)

        self.model = LlamaForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
        )

    def set_parameters(self, params):
        self.params.update(params)
        # set default model from the category

        if "model_name" not in self.params:
            raise RuntimeError("Parameter --model_name not set")

        self.model_name = "meta-llama/" + self.params["model_name"]

    def run(self, queries: Iterator[dict[str, str]]) -> Iterator[dict[str, Any]]:
        dataset = QueryDataset(queries)

        def custom_collate_fn(batch):
            return batch

        # TODO: check how to batch on the number of tokens here
        data_loader = DataLoader(
            dataset,
            batch_size=self.params.get("batch_size", 10),
            shuffle=False,
            collate_fn=custom_collate_fn,
        )

        for i, batch_inputs in enumerate(tqdm.tqdm(data_loader, desc="Processing batches")):
            responses = self.generate(batch_inputs)
            yield from self.process_results(i, batch_inputs, responses)

    def generate(self, batch_inputs, **kwargs):
        queries = [inputs["query"] for inputs in batch_inputs]

        input_tensors = self.tokenizer(queries, return_tensors="pt", padding=True)
        input_ids: torch.Tensor = input_tensors.input_ids
        attention_mask: torch.Tensor = input_tensors.attention_mask

        batch_input_length = input_ids.shape[1]
        max_completion_length = batch_input_length + self.params.get("max_tokens", 0)

        with torch.no_grad():
            try:
                outputs = self.model.generate(
                    input_ids=input_ids.to(self.model.device),
                    attention_mask=attention_mask.to(self.model.device),
                    max_length=max_completion_length,
                    num_return_sequences=self.params.get("num_responses"),
                    top_p=self.params.get("top_p"),
                    top_k=self.params.get("top_k"),
                    do_sample=True,
                    output_scores=True,
                    low_memory=True,
                    return_dict_in_generate=True,
                    max_new_tokens=10,
                    **kwargs,
                )
                return outputs
            except RuntimeError as e:
                print(f"Error during generation: {e}")
                print(f"Input shape: {input_ids.shape}")
                print(f"Attention mask shape: {attention_mask.shape}")
                print(f"Device: {self.model.device}")
                raise

    def process_results(self, batch_id, batch_inputs, outputs):
        generated_sequences = outputs.sequences
        scores = outputs.scores

        for i, inputs in enumerate(batch_inputs):
            query = inputs["query"]

            start_idx = i * self.params.get("num_responses")
            end_idx = (i + 1) * self.params.get("num_responses")

            batch_sequences = generated_sequences[start_idx:end_idx]
            batch_scores = [score[start_idx:end_idx] for score in scores]

            input_tokens = self.tokenizer.encode(query)
            input_token_count = len(input_tokens)

            for _, (seq, seq_scores) in enumerate(
                zip(batch_sequences, zip(*batch_scores))
            ):
                response_text = self.tokenizer.decode(seq, skip_special_tokens=True)
                response_text = (
                    response_text[len(query):]
                    .strip()
                    .replace("\n", " ")
                    .replace("\t", " ")
                )

                output_tokens = self.tokenizer.encode(response_text)
                output_token_count = len(output_tokens)

                # Calculate log probabilities
                log_probs = torch.log_softmax(torch.stack(seq_scores), dim=-1)
                top_log_probs, top_indices = log_probs.topk(5, dim=-1)

                top_tokens = [
                    self.tokenizer.decode([idx.item()]) for idx in top_indices[-1]
                ]
                top_tokens_logprobs = top_log_probs[-1].tolist()

                question_number = batch_id * len(batch_inputs) + i

                yield inputs | {
                    "question number": question_number,
                    "input": input,
                    "query": query,
                    "responses": response_text,
                    "top tokens": top_tokens,
                    "top tokens logprobs": top_tokens_logprobs,
                    "input token count": input_token_count,
                    "output token count": output_token_count,
                }

    def tokenize(self, queries):
        inputs = self.tokenizer(queries, return_tensors="pt", padding=True)
        return inputs["input_ids"], inputs["attention_mask"]
