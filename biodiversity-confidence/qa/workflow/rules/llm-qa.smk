from math import ceil


rule submit_query_batch_to_llm:
    input:
        config["qa_input"],
    output:
        "results/llm/batches/{first}-{last}.tsv",
    log:
        "logs/llm/batches/{first}-{last}.tsv",
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
            --model-category {params.model_family}\
            --model-name {params.model_name}\
            {params.qa_args}\
            {params.qa_questions}\
        1> {output} 2> {log}
        """


rule collect_llm_responses:
    input:
        lambda wildcards: get_batches(namespace="llm"),
    output:
        "results/llm/responses.tsv",
    log:
        "logs/llm/responses.tsv",
    shell:
        "mlr --tsvlite cat {input} > {output}"
