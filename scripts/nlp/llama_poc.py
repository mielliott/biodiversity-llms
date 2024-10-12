from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Get the model from online
base_model = "meta-llama/Llama-3.2-1B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(base_model)

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    return_dict=True,
    low_cpu_mem_usage=True,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id
if model.config.pad_token_id is None:
    model.config.pad_token_id = model.config.eos_token_id

# Your question as a string
prompt = "Does Acer saccharum naturally occur in Arkansas? Yes or no"

# Tokenize the input
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

# Generate a response with additional parameters
outputs = model.generate(
    **inputs,
    max_new_tokens=1,
    do_sample=True,
    temperature=0.7,
    top_k=50,
    top_p=0.95,
    repetition_penalty=1.2,
    length_penalty=1.0,
    no_repeat_ngram_size=3,
    num_return_sequences=1,
    early_stopping=True
)

# Decode and print the generated text
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f'generated_text: {generated_text}')