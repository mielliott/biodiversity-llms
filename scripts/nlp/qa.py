# Submit questions to GPT 3.5.
#
# Usage:
#  echo [TSV lines] | python qa.py [question]
#
# Plug in field values using the field name, e.g. "Who is {name}?"
# e.g. echo -e "species\tlocation\nAcer saccharum\tArkansas" | python qa.py "Does {species} naturally occur in {location}? Yes or no"

import argparse
import os
import sys
import time
from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.nn.functional import softmax

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

def unescape(string):
    if '"' == string[0] == string[-1] or "'" == string[0] == string[-1]:
        return eval(string)
    else:
        return string

def get_questions(patterns, header, lines, do_unescape, filter=lambda x: True):
    fields = header.split("\t")

    for line in lines:
        line = line.strip()
        values = line.split("\t")
        
        if do_unescape:
            values = [v for v in map(unescape, values)]
        
        for pattern in patterns:
            if filter(line):
                field_values = dict(zip(fields, values))
                yield (line, pattern.format(**field_values))

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

def run_openai_model(model, header_in, max_tokens, num_responses, top_p, combine_responses, timeout, escape):
    print(header_in, "query", "responses", "input token count", "output token count", "question number", sep="\t")

    for i, (input, question) in enumerate(questions):
        # See https://platform.openai.com/docs/api-reference/chat/create
        response = query_openai(model, question, n=num_responses, top_p=top_p, max_tokens=max_tokens, request_timeout=timeout)
        answers = [choice["message"]["content"] for choice in response["choices"]]
        if combine_responses:
            answers = [" ".join(answers)]
        for answer in answers:
            print(input, repr(question), repr(answer) if escape else answer, response.usage.prompt_tokens, response.usage.completion_tokens, i, sep="\t", flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Submit questions to GPT 3.5 turbo")
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--num-responses", "-r", default=10, type=int)
    parser.add_argument("--max-tokens", "-t", default=1, type=int)
    parser.add_argument("--top-p", "-p", default=0.8, type=float)
    parser.add_argument("--filter-keyword", "-f", default="MISSING", type=str)
    parser.add_argument("--combine_responses", "-c", action="store_true")
    parser.add_argument("--timeout", default=10, type=int)
    parser.add_argument("--unescape-input", action="store_true")
    parser.add_argument("--escape-responses", action="store_true")
    parser.add_argument("--test", "-x", action="store_true")
    args = parser.parse_args()

    sys.stdin.reconfigure(encoding='utf-8')
    lines = (line for line in sys.stdin)
    header_in = next(lines).rstrip() # Get header of input data
    questions = get_questions(args.patterns, header_in, (l for l in lines), args.unescape_input, lambda query: args.filter_keyword not in query)

    if args.test:
        for q in questions:
                print(q[1])
    else:
        gpt3 = "gpt-3.5-turbo-0613"
        gpt4 = "text-davinci-003"
        run_openai_model(
            gpt3,
            header_in,
            num_responses=args.num_responses,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
            combine_responses=args.combine_responses,
            timeout=args.timeout,
            escape=args.escape_responses
        )
