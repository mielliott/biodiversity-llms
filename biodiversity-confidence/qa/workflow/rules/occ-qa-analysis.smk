rule occqa_make_training_and_test_sets:
    input:
        f"{inputs}/all-shuffled-{config['random_seed']}.tsv"
        if config["qa"]["occurrence"]["shuffle"]
        else f"{inputs}/all.tsv",
    output:
        f"{inputs}/train_test_split.tsv",
    params:
        query_fields=config["qa"]["occurrence"]["query_fields"],
        seed=config["results"]["random_seed"],
        split_rank=config["results"]["train_test_split_rank"],
        split_test_fraction=config["results"]["split_test_fraction"],
    script:
        "../scripts/split_training_test_sets.py"


rule occqa_analyze_results:
    input:
        responses=f"{outputs}/occurrence/responses.tsv",
        taxonomy_scores=f"{outputs}/taxonomy/summary.tsv",
        taxonomy=f"{inputs}/taxa-genus.tsv",
        taxon_counts="resources/idigbio-sample/taxon-counts.tsv",
        train_test_split=f"{inputs}/train_test_split.tsv",
    output:
        f"{outputs}/{config['results']['notebook']}",
    params:
        phrasings=lambda wildcards: config["qa"]["occurrence"]["query_templates"],
        query_fields=config["qa"]["occurrence"]["query_fields"],
        seed=config["results"]["random_seed"],
        validate_absences=config["results"]["validate_absences"],
    log:
        notebook=f"{outputs}/{config['results']['notebook']}",
    conda:
        "../envs/analysis.yml"
    notebook:
        "../notebooks/" + config["results"]["notebook"]
