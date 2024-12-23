import os
from math import ceil


rule submit_query_batch_to_batch_api:
    input:
        config["qa_input"],
    output:
        "results/batch-api/batches/{first}-{last}.tsv",
    log:
        "logs/batch-api/batches/{first}-{last}.tsv",
    params:
        qa_command=config["qa_command"],
        qa_args=qa_command_args,
        qa_questions=lambda w: qa_questions,
        model_family=config["llm_family"],
        model_name=config["llm_model"],
    conda:
        qa_command_env
    shell:
        """
        cat {input}\
        | mlr --tsvlite head -n $(({wildcards.last} + 1))\
            then tail -n $(({wildcards.last} - {wildcards.first} + 1))\
        | {params.qa_command}\
            --model-category batch_{params.model_family}\
            --model-name {params.model_name}\
            --batch write\
            {params.qa_args}\
            {params.qa_questions}\
        1> {output} 2> {log}
        """


rule submit_all_query_batches_to_batch_api:
    input:
        lambda wildcards: get_batches(namespace="batch-api"),
    output:
        "results/batch-api/submit",
    log:
        "logs/batch-api/submit",
    shell:
        """
        touch {output}
        """


rule download_batch_api_results:
    input:
        lambda wildcards: get_batches(namespace="batch-api"),
    output:
        "results/batch-api/results.tsv",
    log:
        "logs/batch-api/results.tsv",
    params:
        qa_command=config["qa_command"],
        qa_args=qa_command_args,
        qa_questions=lambda w: qa_questions,
        model_family=config["llm_family"],
        model_name=config["llm_model"],
    conda:
        os.path.expandvars(config["qa_command_env"])
    shell:
        """
        mlr --tsv cat {input}\
        | {params.qa_command}\
            --model-category batch_{params.model_family}\
            --model-name {params.model_name}\
            --batch read\
            {params.qa_args}\
        1> {output} 2> {log}
        """


rule form_batch_api_responses:
    input:
        queries=config["qa_input"],
        results="results/batch-api/results.tsv",
    output:
        "results/batch-api/responses.tsv",
    log:
        "logs/batch-api/responses.tsv",
    shell:
        """
        mlr --tsv join -j query_number -f {input.queries} {input.results}\
        | mlr --tsv reorder -f query_number,pattern_number\
        > {output}
        """
