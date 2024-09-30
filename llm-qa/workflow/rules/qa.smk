def get_batches(wildcards):
    from math import ceil
    batch_size = config["batch_size"]
    num_lines = sum(1 for line in open(config["input"])) - 1 # Don't count the header line
    
    # print("INPUT IS ", config["input"])
    # print("NUM LINES IS", num_lines)
    # print("OUTPUTS_DIR IS ", OUTPUTS_DIR)
    limit = num_lines if config["query_limit"] <= 0 else min(num_lines, config["query_limit"])
    # print("Batches: ", [get_batch_path(batch, batch_size, limit) for batch in range(ceil(limit / batch_size))])
    return [get_batch_path(batch, batch_size, limit) for batch in range(ceil(limit / batch_size))]

def get_batch_path(batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    return f"{BATCH_OUTPUTS_DIR}/{first}-{last}.tsv"

rule qa:
    input:
        ancient(get_batches)
    output:
        OUTPUTS_DIR + "/responses.tsv"
    shell:
        "mlr --tsvlite cat {input} > {output}"

rule qa_batch:
    input:
        config["input"]
    output:
        BATCH_OUTPUTS_DIR + "/{first}-{last}.tsv"
    params:
        qa_command=config["command"],
        qa_args=" ".join(config["args"] + [f"--model {config['llm']}"]),
        qa_questions=lambda wildcards: " ".join([f'"{q} {config["query_suffix"]}"' for q in config["query_templates"]])
    log:
        "logs/" + BATCH_OUTPUTS_DIR + "/{first}-{last}.tsv"
    conda:
        "envs/qa.yml"
    shell:
        """
        workflow/scripts/cat-range {input} {wildcards.first} {wildcards.last}\
        | {params.qa_command} {params.qa_args} {params.qa_questions}\
        1> {output} 2> {log}
        """
