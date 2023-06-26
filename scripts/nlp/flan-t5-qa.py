# from transformers import T5Tokenizer, T5ForConditionalGeneration
# tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-xxl")
# model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-xxl", device_map="auto")

from transformers import LlamaForCausalLM, LlamaTokenizer
tokenizer = LlamaTokenizer.from_pretrained("/home/mielliott/llama/hf/7B")
model = LlamaForCausalLM.from_pretrained("/home/mielliott/llama/hf/7B", device_map="auto")

def qa(q):
    if type(q) == str:
        q = [q]
    text = q #[f"Me: {qi}\nYou: " for qi in q]
    input_ids = tokenizer(text, return_tensors="pt").input_ids.to("cuda")
    outputs = model.generate(input_ids, max_new_tokens=100, return_dict_in_generate=True, output_scores=True)
    print(f"Me: {q[0]}")
    print(f"AI: {tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)}")
    # return outputs
