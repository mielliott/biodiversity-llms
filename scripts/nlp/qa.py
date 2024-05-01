# Submit questions to an LLM.
#
# Usage:
#  echo [TSV lines] | python qa.py [question] [parameters]
#
# Plug in field values using the field name, e.g. "Who is {name}?"
# e.g. echo -e "species\tlocation\nAcer saccharum\tArkansas" | python qa.py "Does {species} naturally occur in {location}? Yes or no"
#
# See parameters below

import os
import sys
import argparse

from models.openai import GPT
from models.llama2 import Llama2
import util

HUGGING_FACE_TOKEN = os.getenv("ME_HUGGINGFACE_ACCESS")

MODELS = {
    "gpt-3.5-turbo-0613": lambda args: GPT("gpt-3.5-turbo-0613", args.max_tokens, args.timeout, args.top_p),
    "gpt-4-1106-preview": lambda args: GPT("gpt-4-1106-preview", args.max_tokens, args.timeout, args.top_p),
    "llama2-7b": lambda args: Llama2("meta-llama/Llama-2-7b-hf", args.max_tokens, args.num_responses, args.top_p, args.top_k, args.api_access_key or HUGGING_FACE_TOKEN)
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Submit questions to GPT 3.5 turbo")
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--model", "-m", default="gpt-3.5-turbo-0613", type=str, choices=MODELS)
    parser.add_argument("--api-access-key", "-a", default=None, type=str)
    parser.add_argument("--num-responses", "-r", default=10, type=int)
    parser.add_argument("--max-tokens", "-t", default=1, type=int)
    parser.add_argument("--top-p", "-p", default=0.8, type=float)
    parser.add_argument("--top-k", "-k", default=5, type=int)
    parser.add_argument("--filter-keyword", "-f", default="MISSING", type=str)
    parser.add_argument("--combine-responses", "-c", action="store_true")
    parser.add_argument("--timeout", default=10, type=int)
    parser.add_argument("--unescape-input", action="store_true")
    parser.add_argument("--escape-responses", action="store_true")
    parser.add_argument("--test", "-x", action="store_true")
    args = parser.parse_args()

    sys.stdin.reconfigure(encoding='utf-8')
    lines = (line for line in sys.stdin)

    header = next(lines)[:-1] # Get header of input data

    queries = util.get_queries(
        args.patterns, header,
        (l for l in lines),
        args.unescape_input,
        lambda query: args.filter_keyword not in query
    )

    if args.test:
        for q in queries:
            print(q[1])
    else:
        model = MODELS[args.model](args)
        qa = model.run(
            queries=queries,
            num_responses=args.num_responses,
            combine_responses=args.combine_responses,
            escape=args.escape_responses
        )

        write = lambda *args: print(*args, sep="\t")

        for i, (input, output) in enumerate(qa):
            # Print header on the first line
            if i == 0:
                write(header, *output.keys())

            # Print inputs and outputs
            write(input, *output.values())
