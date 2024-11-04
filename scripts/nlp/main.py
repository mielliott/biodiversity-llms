# Submit questions to an LLM.
#
""" 
Usage:
    echo [TSV lines] | python qa.py [question] [parameters]
    Plug in field values using the field name, e.g. "Who is {name}?"

e.g. 
    echo -e "species\tlocation\nAcer saccharum\tArkansas" | python scripts/nlp/main.py -mc "meta-llama" -m "Llama-3.1-8B" "Does {species} naturally occur in {location}? Yes or no"

Run it as a python module by checking out the parent directory.

"""

import argparse
from models.registry import ModelRegistry
from runner import ExperimentRunner

def main():
    parser = argparse.ArgumentParser(description="Submit your questions to LLM of your choice")
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--model-category", "-mc", default="open-ai", type=str, choices=ModelRegistry.list_models())
    parser.add_argument("--model-name", "-m", default="gpt-3.5-turbo-0125", type=str)
    parser.add_argument("--api-access-key", "-a", default=None, type=str)
    parser.add_argument("--num-responses", "-r", default=2, type=int)
    parser.add_argument("--max-tokens", "-t", default=1, type=int)
    parser.add_argument("--top-p", "-p", default=0.95, type=float)
    parser.add_argument("--top-k", "-k", default=2, type=int)
    parser.add_argument("--combine-responses", "-c", action="store_true")
    parser.add_argument("--timeout", default=10, type=int)
    parser.add_argument("--unescape-input", action="store_true")
    parser.add_argument("--test", "-x", action="store_true")
    parser.add_argument("--batch-size", "-bs", default=10, action="store_true")
    parser.add_argument("--temperature", "-temp", default=0.1)
    
    # Convert args to dict for easier handling
    args = parser.parse_args()
    params = vars(args)
    # Call LLM
    runner = ExperimentRunner(args.model_category, params)
    queries = runner.ioHandler.generate_query(
        args.patterns,
        args.unescape_input,
        lambda query: args.filter_keyword not in query
    )

    runner.run_experiment(queries)


if __name__ == "__main__":
    main()