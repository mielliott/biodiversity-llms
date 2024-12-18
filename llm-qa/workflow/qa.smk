from math import ceil


def get_batches(wildcards):
    batch_size = config["batch_size"]
    num_lines = (
        sum(1 for line in open(config["input"])) - 1
    )  # Don't count the header line

    limit = (
        num_lines
        if config["query_limit"] <= 0
        else min(num_lines, config["query_limit"])
    )

    return (
        get_batch_path(batch, batch_size, limit)
        for batch in range(ceil(limit / batch_size))
    )


def get_batch_path(batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    return f"results/batches/{first}-{last}.tsv"


rule answer_questions:
    input:
        get_batches,
    output:
        "results/responses.tsv",
    shell:
        "mlr --tsvlite cat {input} > {output}"


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


rule answer_questions_batch:
    input:
        config["input"],
    output:
        "results/batches/{first}-{last}.tsv",
    params:
        prep_command=config["prep_command"],
        qa_command=config["command"],
        qa_args=" ".join(config["args"]),
        qa_questions=lambda wildcards: " ".join(
            [f'"{q} {config["query_suffix"]}"' for q in config["query_templates"]]
        ),
    log:
        "logs/" + BATCH_OUTPUTS_DIR + "/{first}-{last}.tsv",
    shell:
        """
        cat {input}\
        | mlr --tsvlite head -n $(({wildcards.last} + 1))\
        | mlr --tsvlite tail -n $(({wildcards.last} - {wildcards.first} + 1))\
        | {params.prep_command} \
        | {params.qa_command} {params.qa_args} {params.qa_questions}\
        1> {output} 2> {log}
        """
