rule taxqa_analyze_results:
    input:
        alignments="results/input/alignments.tsv",
        bad_names="results/input/bad-names.tsv",
        responses=f"results/{LLM}/taxonomy/responses.tsv",
    output:
        notebook=TAXQA_NOTEBOOK_OUT,
        summary=f"results/{LLM}/taxonomy/summary.tsv"
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
