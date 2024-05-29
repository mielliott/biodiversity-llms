rule occqa_make_training_and_test_sets:
    input:
        ALL_IN_SHUFFLED if config["qa"]["occurrence"]["shuffle"] else ALL_IN_UNSHUFFLED
    output:
        TRAIN_TEST_SPLIT
    params:
        query_fields=config["qa"]["occurrence"]["query_fields"],
        seed=config["results"]["random_seed"],
        split_rank=config["results"]["train_test_split_rank"],
        split_test_fraction=config["results"]["split_test_fraction"]
    script:
        "../scripts/split-training-test-sets.py"

rule occqa_analyze_results:
    input:
        responses=f"results/{JOB}/{LLM}/occurrence/responses.tsv",
        taxonomy_scores=f"results/{JOB}/{LLM}/taxonomy/summary.tsv",
        taxonomy=f"results/{JOB}/input/taxa-genus.tsv",
        taxon_counts="resources/idigbio-sample/taxon-counts.tsv",
        train_test_split=TRAIN_TEST_SPLIT,
    output:
        NOTEBOOK_OUT
    params:
        phrasings=lambda wildcards: config["qa"]["occurrence"]["query_templates"],
        query_fields=config["qa"]["occurrence"]["query_fields"],
        seed=config["results"]["random_seed"],
        validate_absences=config["results"]["validate_absences"]
    log:
        notebook=NOTEBOOK_OUT
    conda:
        "../envs/analysis.yml"
    notebook:
        "../notebooks/" + config["results"]["notebook"]
