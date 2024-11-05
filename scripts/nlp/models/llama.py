import os
import torch
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoConfig, LlamaForCausalLM
from .registry import ModelRegistry
from .model import Model
from .query import Queries
from torch.utils.data import DataLoader
import tqdm


@ModelRegistry.register("meta-llama")
class Llama(Model):
    def __init__(self):
        load_dotenv(override=True, verbose=True)
        self.params: Dict[str, Any] = {}
        self.model = None
        # default
        self.model_name = "meta-llama/Llama-3.1-8B"
        self.token = os.getenv("HF_TOKEN")
        self.model_cache_dir = os.getenv("HF_HOME", "/storage/hf-models/cache/")

        assert (
            self.token
        ), "Environment variable HF_TOKEN not defined. Generate a token at https://huggingface.co/settings/tokens."

        print("Using HuggingFace cache directory", self.model_cache_dir)

    def get_model_info(self) -> dict:
        return {
            "family": "Meta-Llama",
            "version": "3.2-1b-Instruct",
            "name": self.model_name,
            "provider": "Hugging Face",
            "device": self.model.device,
            "precision": self.params.get("precision", "float32"),
        }

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, token=self.token
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        self.config = AutoConfig.from_pretrained(self.model_name)

        precision_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }

        precision = self.params.get("precision", "float32")
        torch_dtype = precision_map.get(precision, torch.float32)

        self.model = LlamaForCausalLM.from_pretrained(
            self.model_name,
            cache_dir=self.model_cache_dir,
            token=self.token,
            device_map="auto",
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
        )

    def set_parameters(self, params):
        self.params.update(params)
        # set default model from the category
        self.model_name = "meta-llama/" + self.params.get("model_name", "Llama-3.1-8B")

    def run(self, queries: List[Tuple[str, str]]):
        dataset = Queries(queries)

        def custom_collate_fn(batch):
            return batch

        # TODO: check how to batch on the number of tokens here
        dataloader = DataLoader(
            dataset,
            batch_size=self.params.get("batch_size", 10),
            shuffle=False,
            collate_fn=custom_collate_fn,
        )

        all_results = []
        for batch_idx, batch in enumerate(
            tqdm.tqdm(dataloader, desc="Processing batches")
        ):
            if len(batch) < 2:
                inputs, queries = batch[0]
                queries = [queries]
                inputs = [inputs]
            else:
                inputs, queries = zip(*batch)
            responses = self.generate(
                queries,
            )
            all_results.extend(
                self.process_results(inputs, queries, responses, batch_idx)
            )

        return all_results

    def generate(self, queries, **kwargs):
        input_ids, attention_mask = self.tokenize(queries)
        batch_input_length = input_ids.shape[1]
        max_completion_length = batch_input_length + self.params.get("max_tokens", 512)
        with torch.no_grad():
            try:
                outputs = self.model.generate(
                    input_ids=input_ids.to(self.model.device),
                    attention_mask=attention_mask.to(self.model.device),
                    max_length=max_completion_length,
                    num_return_sequences=self.params.get("num_responses", 1),
                    top_p=self.params.get("top_p", 0.95),
                    top_k=2,
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

    def process_results(self, inputs, queries, outputs, batch_idx):
        results = []
        generated_sequences = outputs.sequences
        scores = outputs.scores

        for i, (input, query) in enumerate(zip(inputs, queries)):
            start_idx = i * self.params.get("num_responses", 1)
            end_idx = (i + 1) * self.params.get("num_responses", 1)

            batch_sequences = generated_sequences[start_idx:end_idx]
            batch_scores = [score[start_idx:end_idx] for score in scores]

            input_tokens = self.tokenizer.encode(query)
            input_token_count = len(input_tokens)

            for _, (seq, seq_scores) in enumerate(
                zip(batch_sequences, zip(*batch_scores))
            ):
                response_text = self.tokenizer.decode(seq, skip_special_tokens=True)
                response_text = (
                    response_text[len(query) :]
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

                question_number = batch_idx * len(inputs) + i + 1

                results.append(
                    {
                        "question number": question_number,
                        "input": input,
                        "query": query,
                        "responses": response_text,
                        "top tokens": top_tokens,
                        "top tokens logprobs": top_tokens_logprobs,
                        "input token count": input_token_count,
                        "output token count": output_token_count,
                    }
                )

        return results

    def tokenize(self, queries):
        inputs = self.tokenizer(queries, return_tensors="pt", padding=True)
        return inputs["input_ids"], inputs["attention_mask"]
