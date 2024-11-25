import os

outputs = config["outputs"]

if "shuffle" in config and config["shuffle"]:
    batch_outputs = f"{outputs}/{config['batch_size']}-shuffled-{config['random_seed']}"
else:
    batch_outputs = f"{outputs}/{config['batch_size']}"


def get_batches(wildcards):
    from math import ceil

    batch_size = config["batch_size"]
    num_lines = (
        sum(1 for line in open(config["input"])) - 1
    )  # Don't count the header line

    limit = (
        num_lines
        if config["query_limit"] <= 0
        else min(num_lines, config["query_limit"])
    )
    return [
        get_batch_path(batch, batch_size, limit).format(**wildcards)
        for batch in range(ceil(limit / batch_size))
    ]


def get_batch_path(batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    path = f"{batch_outputs}/{first}-{last}.tsv"
    return path


print(
    get_batch_path(50, 10, 100).format(
        **{"recordset_hash": "8f0594be7f88e4fc7b30c0854e7ca029"}
    )
)


rule answer_questions:
    input:
        ancient(get_batches),
    output:
        f"{outputs}/responses.tsv",
    shell:
        "mlr --tsvlite cat {input} > {output}"


def convert_snake_case_to_hyphens(arg_name: str):
    return arg_name.replace("_", "-")


def convert_args_dict_to_cli(args: dict):
    return " ".join(
        f'--{convert_snake_case_to_hyphens(arg)} "{value}"'.lower()
        for arg, value in config["args"].items()
    )


if not isinstance(config["args"], dict):
    raise RuntimeError("Command args must be a dict. Not this:", config["args"])


rule answer_questions_batch:
    input:
        config["input"],
    output:
        batch_outputs + "/{first}-{last}.tsv",
    params:
        prep_command=config["prep_command"],
        qa_command=config["command"],
        qa_args=convert_args_dict_to_cli(config["args"]),
        qa_questions=lambda wildcards: " ".join(
            [f'"{q} {config["query_suffix"]}"' for q in config["query_templates"]]
        ),
    log:
        "logs/" + batch_outputs + "/{first}-{last}.tsv",
    conda:
        os.path.expandvars(config["command_env"])
    shell:
        """
        workflow/scripts/cat-range {input} {wildcards.first} {wildcards.last}\
        | {params.prep_command} \
        | {params.qa_command} {params.qa_args} {params.qa_questions}\
        1> {output} 2> {log}
        """
