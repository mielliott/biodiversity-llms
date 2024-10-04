

# Setup Llama 3
## 1. Llama3 package by Meta

- install the llama3 package:
    1. download the `meta-llama/llama3` from github 
    2. ``` pip install -e . ```

- run the model:
    1. checkout to the parent model weights directory. 
    2. then run:

```bash 
torchrun --nproc_per_node 1 example_text_completion.py /
--ckpt_dir Llama3.2-1B-Instruct /     
--tokenizer_path Llama3.2-1B-Instruct/tokenizer.model /
--max_seq_len 512 /
--max_batch_size 6
```

### Issues 

1. While running the Llama-3 model params.json has an additional parameter - `use_scaled_rope` this need to be declared in the `llama3/llama/model.py` file. Before building the llama3 package (step-1).
2. During installation of llama3 as a package Tiktoken sometimes does not work and as a work around `rust` compiler installation is required.

## 2. Huggingface -

1. clone the `huggingface/transformers` library from github.
2. convert downloaded weights to huggingface format.
```bash
python src/transformers/models/llama/convert_llama_weights_to_hf.py --input_dir /home/nitingoyal/storage/models/llama3/Llama3.2-3B-Instruct --model_size 1B --output_dir /home/nitingoyal/storage/hf-models/meta-llama3.2-3B-instruct --llama_version 3
```
3. load the converted weights in hugging face from the path.
```python
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

base_model = "/home/nitingoyal/storage/hf-models/meta-llama3.1-8B-instruct"
tokenizer = AutoTokenizer.from_pretrained(base_model)
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    return_dict=True,
    low_cpu_mem_usage=True,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)
```
