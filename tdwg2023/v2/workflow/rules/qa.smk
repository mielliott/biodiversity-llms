QA_BATCH_SIZE = config["qa"]["batch_size"]
BATCH_RESULTS_DIR = f"results/{LLM}/{str(QA_BATCH_SIZE)}"

def get_batches(wildcards):
    from math import ceil
    batch_size = config["qa"]["batch_size"]
    num_lines = sum(1 for line in open(checkpoints.filter_raws_to_presence_tsv.get(**wildcards).output[0])) - 1 # Don't count the header line
    limit = num_lines if config["qa"]["query_limit"] <= 0 else min(num_lines, config["qa"]["query_limit"])
    return [get_batch_path(wildcards, batch, batch_size, limit) for batch in range(ceil(limit / batch_size))]

def get_batch_path(wildcards, batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    return f"{BATCH_RESULTS_DIR}/{wildcards.group}/{first}-{last}.tsv"

rule qa_presence_batch:
    input:
        "results/input/{group}.tsv"
    output:
        protected(BATCH_RESULTS_DIR + "/{group}/{first}-{last}.tsv")
    params:
        qa_command=config["qa"]["command"],
        qa_args=" ".join(config["qa"]["args"] + [f"--model {config['llm']}"]),
        qa_questions=lambda wildcards: " ".join([f'"{q} {config["qa"]["query_suffix"]}"' for q in config["qa"]["query_templates"]]),
    log:
        "logs/" + BATCH_RESULTS_DIR + "/{group}/{first}-{last}.tsv"
    conda:
        "../envs/qa.yml"
    shell:
        """
        workflow/scripts/cat-range {input} {wildcards.first} {wildcards.last}\
        | {params.qa_command} {params.qa_args} {params.qa_questions}\
        1> {output} 2> {log}
        """

rule qa:
    input:
        ancient(get_batches)
    output:
        "results/" + LLM + "/{group,[^/]+}.tsv"
    shell:
        "mlr --tsvlite cat {input} > {output}"
