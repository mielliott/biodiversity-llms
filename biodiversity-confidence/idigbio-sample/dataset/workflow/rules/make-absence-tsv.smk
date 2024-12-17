rule create_pseudo_absence_dataset:
    input:
        "results/presence.tsv",
    output:
        temp("results/absence.tsv.unvalidated"),
    log:
        "logs/absence.tsv.unvalidated.tsv",
    params:
        shuffle_fields="country,stateprovince,county",
        seed=config["random_seed"],
    shell:
        """
        paste <(cat {input} | mlr --tsv cut -x -f {params.shuffle_fields})\
              <(cat {input} | mlr --tsv cut -f {params.shuffle_fields} | mlr --tsv --seed {params.seed} shuffle)\
        > {output}
        """


rule validate_absences:
    input:
        f"results/absence.tsv.unvalidated",
    output:
        f"results/absence-valid.tsv",
    log:
        "logs/absence-valid.tsv",
    conda:
        "../envs/download.yml"
    params:
        idigbio_api=config["idigbio_api"],
    shell:
        """
        cat {input}\
        | python3 workflow/scripts/validate_absences.py {params.idigbio_api}\
        1> {output} 2> {log}
        """


rule filter_absences:
    input:
        unvalidated=f"results/absence.tsv.unvalidated",
        validation=f"results/absence-valid.tsv",
    output:
        f"results/absence.tsv",
    log:
        "logs/absence.tsv",
    shell:
        """
        paste <(cat {input.unvalidated})\
              <(cut -f2 {input.validation})\
        | mlr --tsvlite filter '$valid == "True"'\
        | mlr --tsvlite cut -xf "valid"\
        > {output}
        """
