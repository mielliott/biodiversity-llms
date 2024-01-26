from transformers import LlamaForCausalLM, LlamaTokenizer

path_to_llm_weights = "/home/mielliott/llama/hf/13B"

tokenizer = LlamaTokenizer.from_pretrained(path_to_llm_weights)
model = LlamaForCausalLM.from_pretrained(path_to_llm_weights, device_map="auto")
model.tie_weights()

def run(q):
    if type(q) == str:
        q = [q]

    input_ids = tokenizer(q, return_tensors="pt").input_ids.to("cuda")
    outputs = model.generate(input_ids, max_length=20, return_dict_in_generate=True) # output_scores=True
    print(tokenizer.decode(outputs.sequences[0], skip_special_tokens=False))
