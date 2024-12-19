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
    return f"results/local_batches/batches/{first}-{last}.tsv"


rule answer_questions_batch:
    input:
        config["qa"]["input"],
    output:
        "results/local_batches/batches/{first}-{last}.tsv",
    log:
        "logs/local_batches/batches/{first}-{last}.tsv",
    params:
        qa_command=config["qa"]["command"],
        qa_args=qa_command_args,
        qa_questions=lambda w: qa_questions,
        model_family=config["llm"]["family"],
        model_name=config["llm"]["model"],
    conda:
        qa_command_env
    shell:
        """
        cat {input}\
        | mlr --tsvlite head -n $(({wildcards.last} + 1))\
            then tail -n $(({wildcards.last} - {wildcards.first} + 1))\
        | {params.qa_command}\
            --model-category {params.model_family}\
            --model-name {params.model_name}\
            {params.qa_args}\
            {params.qa_questions}\
        1> {output} 2> {log}
        """


rule answer_questions:
    input:
        get_batches,
    output:
        "results/local_batches/responses.tsv",
    log:
        "logs/local_batches/responses.tsv",
    shell:
        "mlr --tsvlite cat {input} > {output}"
