from transformers import AutoTokenizer, AutoModelForCausalLM
import os
token = os.getenv("ME_HUGGINGFACE_ACCESS")

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf", token=token)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf", token=token, device_map="auto")
model.tie_weights()

def run(q: str):
    input_ids = tokenizer([q], return_tensors="pt").input_ids.to("cuda")
    outputs = model.generate(input_ids, max_length=30, return_dict_in_generate=True, output_scores=True)

    completion = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
    # response = completion.lstrip(q).strip()

    k = 5
    top_k = outputs.scores[-1][0].topk(k)
    top_k_token_scores = top_k.values.tolist()
    top_k_token_strings = [tokenizer.decode(t) for t in top_k.indices]
    print(repr(top_k_token_scores))
    print(repr(top_k_token_strings))

run("How do cows know?")

run("Does Nereis vexillosa naturally occur in Marin County, California, United States? Only say yes or no.")
