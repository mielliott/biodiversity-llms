rule create_pseudo_absence_dataset:
    input:
        f"{inputs}/presence.tsv",
    output:
        temp(f"{inputs}/absence.tsv.unvalidated"),
    params:
        shuffle_fields="'country','stateprovince','county'",
        seed=config["random_seed"],
    shell:
        """
        paste <(cat {input} | mlr --tsv cut -x -f {params.shuffle_fields})\
              <(cat {input} | mlr --tsv cut -f {params.shuffle_fields} | mlr --tsv --seed {params.seed} shuffle)\
        > {output}
        """


rule validate_absences:
    input:
        f"{inputs}/absence.tsv.unvalidated",
    output:
        protected(f"{inputs}/absence-valid.tsv"),
    conda:
        "../../envs/analysis.yml"
    script:
        "../../scripts/validate_absences.py"


rule filter_absences:
    input:
        unvalidated=f"{inputs}/absence.tsv.unvalidated",
        validation=ancient(f"{inputs}/absence-valid.tsv"),
    output:
        f"{inputs}/absence.tsv",
    shell:
        """
        paste <(cat {input.unvalidated})\
              <(cut -f2 {input.validation})\
        | mlr --tsvlite filter '$valid == "True"'\
        | mlr --tsvlite cut -xf "valid"\
        > {output}
        """
