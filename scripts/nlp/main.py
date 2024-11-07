# Submit questions to an LLM.
#
"""
Usage:
    echo [TSV lines] | python qa.py [question] [parameters]
    Plug in field values using the field name, e.g. "Who is {name}?"

e.g.
    echo -e "species\tlocation\nAcer saccharum\tArkansas" | python main.py -mc "llama" -m "llama-3.1-8b" "Does {species} naturally occur in {location}? Yes or no"

Run it as a python module by checking out the parent directory.

Models:
    -mc openai -m gpt-3.5-turbo-0125
    -mc llama -m llama-3.1-8b
"""

import argparse
import io
import sys
from typing import cast

from dotenv import load_dotenv
from models.registry import ModelRegistry
from runner import ExperimentRunner
from llm_io import IOHandler
from args import TokenScoresFormat, Params


def main():
    load_dotenv(override=True, verbose=True)

    parser = argparse.ArgumentParser(description="Submit your questions to LLM of your choice")
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--required-fields", "-f", default=[], type=",".split)
    parser.add_argument("--model-category", "-mc", default="gpt", type=str, choices=ModelRegistry.list_models())
    parser.add_argument("--model-name", "-m", default="gpt-3.5-turbo-0125", type=str)
    parser.add_argument("--num-responses", "-r", default=1, type=int)
    parser.add_argument("--max-tokens", "-t", default=128, type=int)
    parser.add_argument("--combine-responses", "-c", action="store_true")
    parser.add_argument("--batch-size", "-bs", default=10, type=int)
    parser.add_argument("--top-p", "-p", default=0.95, type=float)
    parser.add_argument("--top-k", "-k", default=1, type=int)
    parser.add_argument("--temperature", "-temp", default=0.1, type=float)
    parser.add_argument("--precision", "-np", default="bfloat16", type=str)
    parser.add_argument("--timeout", default=10, type=int)
    parser.add_argument("--test", "-x", action="store_true")
    parser.add_argument("--scores", "-s", default=TokenScoresFormat.RESPONSE_TOKENS, **TokenScoresFormat.arg())

    args = parser.parse_args()
    if args.test:
        args.model_category = "test"

    io_handler = IOHandler(
        args.patterns,
        args.required_fields
    )

    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')

    params = cast(Params, args)
    runner = ExperimentRunner(args.model_category, params, io_handler)
    runner.run_experiment(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
