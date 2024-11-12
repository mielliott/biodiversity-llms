rule taxqa_analyze_results:
    input:
        alignments=f"{inputs}/alignments.tsv",
        bad_names=f"{inputs}/bad-names.tsv",
        responses=f"{outputs}/taxonomy/responses.tsv",
    output:
        notebook=f"{outputs}/taxqa-results.py.ipynb",
        summary=f"{outputs}/taxonomy/summary.tsv",
    params:
        phrasings=lambda wildcards: config["qa"]["occurrence"]["query_templates"],
        query_fields=config["qa"]["occurrence"]["query_fields"],
        seed=config["results"]["random_seed"],
        validate_absences=config["results"]["validate_absences"],
    log:
        notebook=f"{outputs}/taxqa-results.py.ipynb",
    conda:
        "../envs/analysis.yml"
    notebook:
        "../notebooks/process-tax.py.ipynb"
