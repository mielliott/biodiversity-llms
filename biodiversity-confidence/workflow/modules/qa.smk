print("QA config:", config, "\n")

if "shuffle" in config and config["shuffle"]:
    BATCH_OUTPUTS_DIR = f"{config['output_dir']}/{config['batch_size']}-shuffled-{config['random_seed']}"
else:
    BATCH_OUTPUTS_DIR = f"{config['output_dir']}/{config['batch_size']}"

def get_batches(wildcards):
    from math import ceil
    batch_size = config["batch_size"]
    num_lines = sum(1 for line in open(config["input"])) - 1 # Don't count the header line
    
    limit = num_lines if config["query_limit"] <= 0 else min(num_lines, config["query_limit"])
    return [get_batch_path(batch, batch_size, limit) for batch in range(ceil(limit / batch_size))]

def get_batch_path(batch, batch_size, limit):
    first = batch * batch_size
    last = min(limit - 1, (batch + 1) * batch_size - 1)
    path = f"{BATCH_OUTPUTS_DIR}/{first}-{last}.tsv"
    return path

rule template_qa:
    input:
        ancient(get_batches)
    output:
        config['output_dir'] + "/responses.tsv"
    shell:
        "mlr --tsvlite cat {input} > {output}"

rule template_qa_batch:
    input:
        config["input"]
    output:
        BATCH_OUTPUTS_DIR + "/{first}-{last}.tsv"
    params:
        prep_command=config["prep_command"],
        qa_command=config["command"],
        qa_args=" ".join(config["args"] + [f"--model {config['llm']}"]),
        qa_questions=lambda wildcards: " ".join([f'"{q} {config["query_suffix"]}"' for q in config["query_templates"]])
    log:
        "logs/" + BATCH_OUTPUTS_DIR + "/{first}-{last}.tsv"
    conda:
        "../envs/qa.yml"
    shell:
        """
        workflow/scripts/cat-range {input} {wildcards.first} {wildcards.last}\
        | {params.prep_command} \
        | {params.qa_command} {params.qa_args} {params.qa_questions}\
        1> {output} 2> {log}
    """
