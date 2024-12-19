# Submit questions to an LLM.
#
"""
Usage:
    echo [TSV lines] | python qa.py [question] [parameters]
    Plug in field values using the field name, e.g. "Who is {name}?"

e.g.
    echo -e "species\tlocation\nAcer saccharum\tArkansas" | python main.py -mc "llama" -m "llama-3.2-1b-instruct" "Does {species} naturally occur in {location}? Yes or no"

Run it as a python module by checking out the parent directory.

Models:
    -mc gpt -m gpt-3.5-turbo-0125
    -mc llama -m llama-3.2-1b-instruct
"""

import argparse
import io
import sys
from typing import cast

from dotenv import load_dotenv
from models.registry import ModelRegistry
from runner import ExperimentRunner
from llm_io import IOHandler
from args import TokenScoresFormat, Params, get_default_params, BatchProcess


def main():
    load_dotenv(override=True, verbose=True)

    parser = argparse.ArgumentParser(description="Submit your questions to LLM of your choice")
    parser.add_argument("patterns", nargs="*")
    parser.add_argument("--required-fields", "-f", default=[], type=",".split)
    parser.add_argument("--model-category", "-mc", default="gpt", type=str, choices=ModelRegistry.list_models())
    parser.add_argument("--test", "-x", action="store_true")

    # Model params
    parser.add_argument("--model-name", "-m", type=str)
    parser.add_argument("--num-responses", "-r", type=int)
    parser.add_argument("--max-tokens", "-t", type=int)
    parser.add_argument("--combine-responses", "-c", action="store_true")
    parser.add_argument("--batch-size", "-bs", type=int)
    parser.add_argument("--top-p", "-p", type=float)
    parser.add_argument("--top-k", "-k", type=int)
    parser.add_argument("--temperature", "-temp", type=float)
    parser.add_argument("--precision", "-np", type=str)
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--scores", "-s", **TokenScoresFormat.arg())
    parser.add_argument("--batch", "-b", **BatchProcess.arg())
    parser.set_defaults(**get_default_params())

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
    runner.run_experiment(sys.stdin)


if __name__ == "__main__":
    main()
