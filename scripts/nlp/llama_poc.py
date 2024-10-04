from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# base_model = "/home/nitingoyal/storage/hf-models/meta-llama3.2-3B-instruct"
# get it from online
# base_model = "meta-llama/Llama-3.2-1B-Instruct"
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

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Your question as a string
prompt = "Who is Vincent van Gogh?"

# Generate a response
outputs = pipe(prompt, max_new_tokens=200, do_sample=True)

# Output generated text
print(outputs[0]["generated_text"])
