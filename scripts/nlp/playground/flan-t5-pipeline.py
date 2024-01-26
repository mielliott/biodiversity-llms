from transformers import T5Tokenizer, T5ForConditionalGeneration, Text2TextGenerationPipeline
from datasets import Dataset

tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-xxl")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-xxl", device_map="auto")

pl = Text2TextGenerationPipeline(model=model, tokenizer=tokenizer)

dataset_path = "/home/mielliott/tdwg2023/idigbio/genus-epithet-country-province-10000.tsv"

gen = (line for line in open(dataset_path, "rt", encoding="utf-8"))
next(gen) # skip header line

def tokenization(example):
    return tokenizer(example).input_ids.to("cuda")

for o in pl(gen, batch_size=2):
    print(o)

ds = Dataset.from_generator(gen)