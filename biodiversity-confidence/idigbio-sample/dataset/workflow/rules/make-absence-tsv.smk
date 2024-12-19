rule create_pseudo_absence_dataset:
    input:
        "results/presence.tsv",
    output:
        "results/absence.tsv",
    log:
        "logs/absence.tsv",
    conda:
        "../envs/download.yml"
    params:
        shuffle_fields=",".join(config["absence_shuffle_fields"]),
        validation_fields=",".join(config["absence_validation_fields"]),
        max_retries=100,
        idigbio_api=config["idigbio_api"],
        random_seed=config["random_seed"],
    shell:
        """
        cat {input}\
        | python3 workflow/scripts/make_absences.py {input} {params.shuffle_fields} {params.validation_fields} {params.max_retries} {params.idigbio_api} {params.random_seed}\
        | mlr --tsvlite uniq -a\
        1> {output} 2> {log}
        """
