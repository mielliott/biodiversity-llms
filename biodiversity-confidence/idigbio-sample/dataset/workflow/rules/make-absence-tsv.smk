rule create_pseudo_absence_dataset:
    input:
        "results/presence.tsv",
    output:
        f"results/absence.tsv",
    log:
        "logs/absence.tsv",
    conda:
        "../envs/download.yml"
    params:
        location_fields="country,stateprovince,county",
        max_retries=100,
        idigbio_api=config["idigbio_api"],
        random_seed=config["random_seed"],
    shell:
        """
        mlr --tsv cut -x -f {params.location_fields} {input}\
        | python3 workflow/scripts/make_absences.py {input} {params.location_fields} {params.max_retries} {params.idigbio_api} {params.random_seed}\
        | mlr --tsv uniq -a\
        1> {output} 2> {log}
        """
