rule taxqa_analyze_results:
    input:
        alignments=f"results/{JOB}/input/alignments.tsv",
        bad_names=f"results/{JOB}/input/bad-names.tsv",
        responses=f"results/{JOB}/{LLM}/taxonomy/responses.tsv",
    output:
        notebook=TAXQA_NOTEBOOK_OUT,
        summary=f"results/{JOB}/{LLM}/taxonomy/summary.tsv"
    params:
        phrasings=lambda wildcards: config["qa"]["occurrence"]["query_templates"],
        query_fields=config["qa"]["occurrence"]["query_fields"],
        seed=config["results"]["random_seed"],
        validate_absences=config["results"]["validate_absences"]
    log:
        notebook=TAXQA_NOTEBOOK_OUT
    conda:
        "../envs/analysis.yml"
    notebook:
        "../notebooks/process-tax.py.ipynb"
