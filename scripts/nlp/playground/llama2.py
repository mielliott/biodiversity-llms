from transformers import LlamaTokenizer, LlamaForCausalLM
import os
import torch

api_access_key = os.getenv("ME_HUGGINGFACE_ACCESS")
model_path = "meta-llama/Llama-2-7b-chat-hf"

tokenizer = LlamaTokenizer.from_pretrained(model_path, token=api_access_key)
tokenizer.pad_token = "[PAD]"
tokenizer.padding_side = "left"

model = LlamaForCausalLM.from_pretrained(model_path, token=api_access_key, device_map="auto", torch_dtype=torch.bfloat16)
model.tie_weights()

queries = ["How do cows know?", "What is the answer to the riddle?"]
queries = ["How do cows know?"]

# We can run inference on about 100 of these queries at a time
queries = ["Is it possible to encounter species Halichondria bowerbanki in French Frigate Shoals, Hawaii, United States? Only respond yes or no."]

input_ids = tokenizer(queries, return_tensors="pt", padding=True).input_ids.to("cuda")
input_length = input_ids.shape[1]
NUM_WHITESPACE_TOKENS = 2
max_completion_length = input_length + NUM_WHITESPACE_TOKENS + 1

outputs = model.generate(input_ids, max_length=max_completion_length, return_dict_in_generate=True, output_scores=True, low_memory=True)

print(tokenizer.decode(outputs.sequences[0], skip_special_tokens=True))

completion = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)

# Free GPU resources
import gc
torch.cuda.empty_cache()
gc.collect()

i = 0
j = 0
ith_token_scores = outputs.scores[i]
jth_query_0th = ith_token_scores[j]

def index_of_first_non_whitespace_token(sequence):
    for i, token in enumerate(sequence):
        token_string = tokenizer.decode(sequence[i].unsqueeze(0))
        if not token_string.isspace():
            return i

sequence_index = 0
sequence = outputs.sequences[sequence_index][input_length:]
i = index_of_first_non_whitespace_token(sequence)

top_k_results = outputs.scores[i][sequence_index].topk(5)
top_k_token_scores = top_k_results.values.tolist()
top_k_token_strings = [tokenizer.decode([t], skip_special_tokens=True).lstrip() for t in top_k_results.indices]
