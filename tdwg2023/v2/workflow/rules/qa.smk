def get_batches(wildcards):
    from math import ceil
    batch_size = config["qa_batch_size"]
    num_lines = sum(1 for line in open(checkpoints.filter_raws_to_presence_tsv.get(**wildcards).output[0])) - 1 # Don't count the header line
    limit = num_lines if config["qa_limit"] <= 0 else min(num_lines, config["qa_limit"])

    return [get_batch_path(wildcards, batch, batch_size, limit) for batch in range(ceil(limit / batch_size))]

def get_batch_path(wildcards, batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    return f"{BATCH_RESULTS_DIR}/{wildcards.group}/{first}-{last}.tsv"

rule qa_presence_batch:
    input:
        "resources/{group}.tsv"
    output:
        BATCH_RESULTS_DIR + "/{group}/{first}-{last}.tsv"
    params:
        qa_command=config["qa_command"],
        qa_args=" ".join(config["qa_args"]),
        qa_questions=lambda wildcards: " ".join([f'"{q} {config["qa_query_suffix"]}"' for q in config["qa_base_queries"]]),
    log:
        "logs/" + BATCH_RESULTS_DIR + "/{group}/{first}-{last}.tsv"
    shell:
        """
        workflow/scripts/cat-range {input} {wildcards.first} {wildcards.last}\
        | {params.qa_command} {params.qa_args} {params.qa_questions}\
        1> {output} 2> {log}
        """

rule qa:
    input:
        get_batches
    output:
        "results/{group,[^/]+}.tsv"
    shell:
        "mlr --tsvlite cat {input} > {output}"