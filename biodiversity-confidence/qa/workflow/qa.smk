import os
from math import ceil


def get_batches(wildcards):
    batch_size = config["qa"]["batch_size"]
    num_lines = (
        sum(1 for line in open(config["qa"]["input"])) - 1
    )  # Don't count the header line

    limit = (
        num_lines
        if config["qa"]["query_limit"] <= 0
        else min(num_lines, config["qa"]["query_limit"])
    )

    return (
        get_batch_path(batch, batch_size, limit)
        for batch in range(ceil(limit / batch_size))
    )


def get_batch_path(batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    return f"results/batches/{first}-{last}.tsv"


def convert_snake_case_to_hyphens(arg_name: str):
    return arg_name.replace("_", "-")


def convert_args_dict_to_cli(args: dict):
    return " ".join(
        f'--{convert_snake_case_to_hyphens(arg)} "{value}"'.lower()
        for arg, value in config["qa"]["command_args"].items()
    )


if not isinstance(config["qa"]["command_args"], dict):
    raise RuntimeError(
        "Command args must be a dict. Not this:", config["qa"]["command_args"]
    )

qa_command_args = convert_args_dict_to_cli(config["qa"]["command_args"])

qa_questions = " ".join(
    [f'"{q} {config["qa"]["query_suffix"]}"' for q in config["qa"]["query_templates"]]
)


rule submit_questions_to_batch_api:
    input:
        config["qa"]["input"],
    output:
        "results/openai_batch.tsv",
    log:
        "logs/openai_batch.tsv",
    params:
        qa_command=config["qa"]["command"],
        qa_args=qa_command_args,
        qa_questions=lambda w: qa_questions,
        model_family=config["llm"]["family"],
        model_name=config["llm"]["model"],
    conda:
        os.path.expandvars(config["qa"]["command_env"])
    shell:
        """
        cat {input}\
        | {params.qa_command}\
            --model-category batch_{params.model_family}\
            --model-name {params.model_name}\
            --batch write\
            {params.qa_args}\
            {params.qa_questions}\
        1> {output} 2> {log}
        """


rule answer_questions:
    input:
        get_batches,
    output:
        "results/responses.tsv",
    shell:
        "mlr --tsvlite cat {input} > {output}"


rule answer_questions_batch:
    input:
        config["qa"]["input"],
    output:
        "results/batches/{first}-{last}.tsv",
    log:
        "logs/batches/{first}-{last}.tsv",
    params:
        qa_command=config["qa"]["command"],
        qa_args=qa_command_args,
        qa_questions=lambda w: qa_questions,
        model_family=config["llm"]["family"],
        model_name=config["llm"]["model"],
    conda:
        os.path.expandvars(config["qa"]["command_env"])
    shell:
        """
        cat {input}\
        | mlr --tsvlite head -n $(({wildcards.last} + 1))\
        | mlr --tsvlite tail -n $(({wildcards.last} - {wildcards.first} + 1))\
        | {params.qa_command}\
            --model-category {params.model_family}\
            --model-name {params.model_name}\
            {params.qa_args}\
            {params.qa_questions}\
        1> {output} 2> {log}
        """
