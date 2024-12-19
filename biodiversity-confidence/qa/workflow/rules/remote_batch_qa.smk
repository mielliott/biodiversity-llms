import os
from math import ceil


rule submit_questions_to_batch_api:
    input:
        config["qa"]["input"],
    output:
        "results/remote_batches/batch_id.tsv",
    log:
        "logs/remote_batches/batch_id.tsv",
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
        | {params.qa_command}\
            --model-category batch_{params.model_family}\
            --model-name {params.model_name}\
            --batch write\
            {params.qa_args}\
            {params.qa_questions}\
        1> {output} 2> {log}
        """


rule download_batch_api_results:
    input:
        "results/remote_batches/batch_id.tsv",
    output:
        "results/remote_batches/batch_results.tsv",
    log:
        "logs/remote_batches/batch_results.tsv",
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
            --batch read\
            {params.qa_args}\
        1> {output} 2> {log}
        """


rule form_batch_api_responses:
    input:
        queries=config["qa"]["input"],
        results="results/remote_batches/batch_results.tsv",
    output:
        "results/remote_batches/responses.tsv",
    log:
        "logs/remote_batches/responsess.tsv",
    shell:
        """
        mlr --tsv join -j query_number -f {input.queries} {input.results}\
        | mlr --tsv reorder -f query_number,pattern_number\
        > {output}
        """
