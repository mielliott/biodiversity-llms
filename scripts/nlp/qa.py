# Submit questions to GPT 3.5.
#
# Usage:
#  echo [TSV lines] | python qa.py [question]
#
# Any "{0}", "{1}", etc. in the question are replaced by columns from the TSV input
# e.g. echo -e "Acer saccharum\tArkansas" | python qa.py "Does {0} naturally occur in {1}? Yes or no"

import os
import sys
import time
from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.nn.functional import softmax

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

def make_question(query, line):
    line = line.split("\t")
    return query.format(*line)

def prep_local_model():
    global tokenizer, model, qa
    tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-xxl")
    model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-xxl", device_map="auto")

    def qa(question):
        i = tokenizer(question, return_tensors="pt", padding=True).input_ids.to("cuda")
        o = model.generate(i, max_new_tokens=200, return_dict_in_generate=True, output_scores=True)
        print(tokenizer.decode(o.sequences[0], skip_special_tokens=True))


def batched(iterable, n):
    args = [iter(iterable)] * n
    return zip(*args)

def run_local_model():
    print("response", "tokens", "log scores", "softmax scores", sep="\t")

    batch_size = 4
    for batch in batched(questions, batch_size):
        i = tokenizer(batch, return_tensors="pt", padding=True).input_ids.to("cuda")
        o = model.generate(i, max_new_tokens=20, return_dict_in_generate=True, output_scores=True)
        
        for iseq, seq in enumerate(o.sequences):
            response = seq[1:-1]
            log_scores = [o.scores[it][iseq][t] for it, t in enumerate(response)]
            softmax_scores = [softmax(o.scores[it][iseq], dim=0)[t] for it, t in enumerate(response)]

            print(tokenizer.decode(response),
                " ".join([str(id) for id in response.tolist()]),
                " ".join(["{:.3f}".format(score.tolist()) for score in log_scores]),
                " ".join(["{:.3f}".format(score.tolist()) for score in softmax_scores]),
                sep="\t",
                flush=True)

# For kwargs see https://platform.openai.com/docs/api-reference/chat/create
def query_openai(model: str, query: str, **kwargs) -> list[str]:
    while (True):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": query}],
                **kwargs
            )
            return response
        
        except Exception as e:
            print("Request failed:", e, file=sys.stderr)
            time.sleep(5)

def run_openai_model(model):
    print("responses", "input token count", "output token count", sep="\t")

    for question in questions:
        # See https://platform.openai.com/docs/api-reference/chat/create
        response = query_openai(model, question, n=10, top_p=0.8, max_tokens=1)
        answers = [choice["message"]["content"] for choice in response["choices"]]
        print(" ".join(answers), response.usage.prompt_tokens, response.usage.completion_tokens, sep="\t", flush=True)

if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    lines = (line for line in sys.stdin)
    next(lines) # skip header line

    query_pattern = "Does {0} {1} naturally occur in {3}, {2}? Yes or no."
    if len(sys.argv) > 1:
        query_pattern = sys.argv[1]

    questions = (make_question(query_pattern, l[:-1]) for l in lines)

    if len(sys.argv) > 2:
        print(next(questions))
    else:
        gpt3 = "gpt-3.5-turbo-0613"
        gpt4 = "text-davinci-003"
        run_openai_model(gpt3)
